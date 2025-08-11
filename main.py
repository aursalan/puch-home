import asyncio
from typing import Annotated, List, Literal, Union
import os
from dotenv import load_dotenv
from fastmcp import FastMCP
from fastmcp.server.auth.providers.bearer import BearerAuthProvider, RSAKeyPair
from mcp import ErrorData, McpError
from mcp.server.auth.provider import AccessToken
from mcp.types import TextContent, ImageContent, INVALID_PARAMS, INTERNAL_ERROR
from pydantic import BaseModel, Field, AnyUrl
import markdownify
import httpx
import readabilipy
import re
import inspect 
import cv2
import base64
import datetime
from onvif import ONVIFCamera, exceptions

# --- Load environment variables ---
load_dotenv()

TOKEN = os.environ.get("AUTH_TOKEN")
MY_NUMBER = os.environ.get("MY_NUMBER")

print(f"--- SERVER TOKEN ON STARTUP: [{TOKEN}] ---")

assert TOKEN is not None, "Please set AUTH_TOKEN in your .env file"
assert MY_NUMBER is not None, "Please set MY_NUMBER in your .env file"

# --- Auth Provider ---
class SimpleBearerAuthProvider(BearerAuthProvider):
    def __init__(self, token: str):
        k = RSAKeyPair.generate()
        super().__init__(public_key=k.public_key, jwks_uri=None, issuer=None, audience=None)
        self.token = token

    async def load_access_token(self, token: str) -> AccessToken | None:
        if token == self.token:
            return AccessToken(
                token=token,
                client_id="puch-client",
                scopes=["*"],
                expires_at=None,
            )
        return None

# --- Rich Tool Description model ---
class RichToolDescription(BaseModel):
    description: str
    use_when: str
    side_effects: str | None = None

# --- Fetch Utility Class ---
class Fetch:
    USER_AGENT = "Puch/1.0 (Autonomous)"

    @classmethod
    async def fetch_url(
        cls,
        url: str,
        user_agent: str,
        force_raw: bool = False,
    ) -> tuple[str, str]:
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    url,
                    follow_redirects=True,
                    headers={"User-Agent": user_agent},
                    timeout=30,
                )
            except httpx.HTTPError as e:
                raise McpError(ErrorData(code=INTERNAL_ERROR, message=f"Failed to fetch {url}: {e!r}"))

            if response.status_code >= 400:
                raise McpError(ErrorData(code=INTERNAL_ERROR, message=f"Failed to fetch {url} - status code {response.status_code}"))

            page_raw = response.text

        content_type = response.headers.get("content-type", "")
        is_page_html = "text/html" in content_type

        if is_page_html and not force_raw:
            return cls.extract_content_from_html(page_raw), ""

        return (
            page_raw,
            f"Content type {content_type} cannot be simplified to markdown, but here is the raw content:\n",
        )

    @staticmethod
    def extract_content_from_html(html: str) -> str:
        """Extract and convert HTML content to Markdown format."""
        ret = readabilipy.simple_json.simple_json_from_html_string(html, use_readability=True)
        if not ret or not ret.get("content"):
            return "<error>Page failed to be simplified from HTML</error>"
        content = markdownify.markdownify(ret["content"], heading_style=markdownify.ATX)
        return content

    @staticmethod
    async def google_search_links(query: str, num_results: int = 5) -> list[str]:
        """
        Perform a scoped DuckDuckGo search and return a list of job posting URLs.
        (Using DuckDuckGo because Google blocks most programmatic scraping.)
        """
        ddg_url = f"https://html.duckduckgo.com/html/?q={query.replace(' ', '+')}"
        links = []

        async with httpx.AsyncClient() as client:
            resp = await client.get(ddg_url, headers={"User-Agent": Fetch.USER_AGENT})
            if resp.status_code != 200:
                return ["<error>Failed to perform search.</error>"]

        from bs4 import BeautifulSoup
        soup = BeautifulSoup(resp.text, "html.parser")
        for a in soup.find_all("a", class_="result__a", href=True):
            href = a["href"]
            if "http" in href:
                links.append(href)
            if len(links) >= num_results:
                break

        return links or ["<error>No results found.</error>"]

# --- MCP Server Setup ---
mcp = FastMCP(
    "Job Finder MCP Server",
    auth=SimpleBearerAuthProvider(TOKEN),
)

# --- Tool: validate (required by Puch) ---
@mcp.tool
async def validate() -> str:
    return MY_NUMBER

# --- Tool: job_finder (now smart!) ---
JobFinderDescription = RichToolDescription(
    description="Smart job tool: analyze descriptions, fetch URLs, or search jobs based on free text.",
    use_when="Use this to evaluate job descriptions or search for jobs using freeform goals.",
    side_effects="Returns insights, fetched job descriptions, or relevant job links.",
)

@mcp.tool(description=JobFinderDescription.model_dump_json())
async def job_finder(
    user_goal: Annotated[str, Field(description="The user's goal (can be a description, intent, or freeform query)")],
    job_description: Annotated[str | None, Field(description="Full job description text, if available.")] = None,
    job_url: Annotated[AnyUrl | None, Field(description="A URL to fetch a job description from.")] = None,
    raw: Annotated[bool, Field(description="Return raw HTML content if True")] = False,
) -> str:
    """
    Handles multiple job discovery methods: direct description, URL fetch, or freeform search query.
    """
    if job_description:
        return (
            f"📝 **Job Description Analysis**\n\n"
            f"---\n{job_description.strip()}\n---\n\n"
            f"User Goal: **{user_goal}**\n\n"
            f"💡 Suggestions:\n- Tailor your resume.\n- Evaluate skill match.\n- Consider applying if relevant."
        )

    if job_url:
        content, _ = await Fetch.fetch_url(str(job_url), Fetch.USER_AGENT, force_raw=raw)
        return (
            f"🔗 **Fetched Job Posting from URL**: {job_url}\n\n"
            f"---\n{content.strip()}\n---\n\n"
            f"User Goal: **{user_goal}**"
        )

    if "look for" in user_goal.lower() or "find" in user_goal.lower():
        links = await Fetch.google_search_links(user_goal)
        return (
            f"🔍 **Search Results for**: _{user_goal}_\n\n" +
            "\n".join(f"- {link}" for link in links)
        )

    raise McpError(ErrorData(code=INVALID_PARAMS, message="Please provide either a job description, a job URL, or a search query in user_goal."))


# Image inputs and sending images

MAKE_IMG_BLACK_AND_WHITE_DESCRIPTION = RichToolDescription(
    description="Convert an image to black and white and save it.",
    use_when="Use this tool when the user provides an image URL and requests it to be converted to black and white.",
    side_effects="The image will be processed and saved in a black and white format.",
)

@mcp.tool(description=MAKE_IMG_BLACK_AND_WHITE_DESCRIPTION.model_dump_json())
async def make_img_black_and_white(
    puch_image_data: Annotated[str, Field(description="Base64-encoded image data to convert to black and white")] = None,
) -> list[TextContent | ImageContent]:
    import base64
    import io

    from PIL import Image

    try:
        image_bytes = base64.b64decode(puch_image_data)
        image = Image.open(io.BytesIO(image_bytes))

        bw_image = image.convert("L")

        buf = io.BytesIO()
        bw_image.save(buf, format="PNG")
        bw_bytes = buf.getvalue()
        bw_base64 = base64.b64encode(bw_bytes).decode("utf-8")

        return [ImageContent(type="image", mimeType="image/png", data=bw_base64)]
    except Exception as e:
        raise McpError(ErrorData(code=INTERNAL_ERROR, message=str(e)))

# --- Helper function for handling awaitables gracefully ---
async def resolve_awaitable(obj):
    if inspect.isawaitable(obj):
        return await obj
    return obj

# -----------------------------
# Smart Home: tools (with camera integration)
# -----------------------------

# --- Load Camera Credentials ---
CAMERA_IP = os.getenv("CAMERA_IP")
ONVIF_PORT = int(os.getenv("ONVIF_PORT", 8000))
ONVIF_USER = os.getenv("ONVIF_USER")
ONVIF_PASS = os.getenv("ONVIF_PASS")

# --- Model ---
class SmartDevice(BaseModel):
    id: str
    name: str
    aliases: List[str] = []
    type: Literal["light", "thermostat", "plug", "camera"]
    online: bool = True
    capabilities: List[str] = []

# --- In-memory device store ---
_SMART_HOME_DEVICE_STORE: dict[str, SmartDevice] = {
    "dev-lamp-1": SmartDevice(id="dev-lamp-1", name="Desk Lamp", aliases=["desk lamp", "lamp"], type="light", capabilities=["on_off"]),
    "dev-therm-1": SmartDevice(id="dev-therm-1", name="Living Thermostat", aliases=["thermostat"], type="thermostat", capabilities=["set_temperature"]),
    "dev-plug-1": SmartDevice(id="dev-plug-1", name="Coffee Plug", aliases=["coffee maker"], type="plug", capabilities=["on_off"]),
    "real-cam-1": SmartDevice(id="real-cam-1", name="Security Camera", aliases=["camera", "security cam"], type="camera", capabilities=["reboot", "get_status", "take_snapshot"]),
}

# --- Structured request model ---
class SmartCommandRequest(BaseModel):
    device_id: str
    command: str
    params: dict | None = None


# --- Lightweight parser ---
def parse_smart_command(user_text: str) -> dict | None:
    t = user_text.lower()
    action = None
    if any(p in t for p in ("turn on", "switch on")):
        action = "turn_on"
    elif any(p in t for p in ("turn off", "switch off")):
        action = "turn_off"
    elif ("set" in t and ("temperature" in t or "thermostat" in t)) or re.search(r"\bset .* to \d{2}\b", t):
        action = "set_temperature"
    elif any(p in t for p in ("status", "state", "is the")):
        action = "get_status"
    elif "reboot" in t:
        action = "reboot"
    elif any(p in t for p in ("snapshot", "picture", "photo")):
        action = "take_snapshot"

    if not action:
        return None

    device_id = None
    for dev in _SMART_HOME_DEVICE_STORE.values():
        if dev.name.lower() in t or any(alias in t for alias in dev.aliases):
            device_id = dev.id
            break

    params: dict = {}
    if action == "set_temperature":
        m = re.search(r"(\d{2})\b", t)
        if m:
            params["temperature"] = int(m.group(1))

    return {"device_id": device_id, "command": action, "params": params}

# --- Discover tool ---
@mcp.tool(description="Discover local/mock smart-home devices (demo)")
async def smart_home_discover() -> str:
    lines = ["Discovered devices:"]
    for d in _SMART_HOME_DEVICE_STORE.values():
        lines.append(f"- {d.id} | {d.name} | aliases={d.aliases} | type={d.type} | caps={d.capabilities} | online={d.online}")
    return "\n".join(lines)

# --- Execute structured command ---
@mcp.tool(description="Execute a structured smart-home command (mock or real).")
async def smart_home_execute(
    req: Annotated[SmartCommandRequest, Field(description="Structured smart-home command payload")]
) -> Union[str, list[ImageContent]]:
    device = _SMART_HOME_DEVICE_STORE.get(req.device_id)
    if not device:
        raise McpError(ErrorData(code=INVALID_PARAMS, message=f"Device {req.device_id} not found"))

    # --- MOCK DEVICE LOGIC ---
    if device.type in ["light", "plug", "thermostat"]:
        if req.command == "turn_on": return f"OK: Mock {device.name} is now ON"
        if req.command == "turn_off": return f"OK: Mock {device.name} is now OFF"
        if req.command == "get_status": return f"OK: Mock {device.name} is {'online' if device.online else 'offline'}"
        if req.command == "set_temperature":
            temp = req.params.get("temperature") if req.params else None
            if temp is None: raise McpError(ErrorData(code=INVALID_PARAMS, message="Missing temperature"))
            return f"OK: Mock {device.name} temperature set to {temp}°C"
    
    # --- REAL CAMERA LOGIC ---
    if device.type == "camera":
        if not all([CAMERA_IP, ONVIF_USER, ONVIF_PASS]):
            return "Error: Camera credentials are not configured on the server."
        
        try:
            mycam = ONVIFCamera(CAMERA_IP, ONVIF_PORT, ONVIF_USER, ONVIF_PASS)
            
            # The .update_xaddrs() call may or may not return a coroutine.
            await resolve_awaitable(mycam.update_xaddrs())
            
            if req.command == "take_snapshot":
                media_service = await resolve_awaitable(mycam.create_media_service())
                if not media_service:
                    return "Error: Could not create media service for camera."

                profiles = await resolve_awaitable(media_service.GetProfiles())
                if not profiles:
                    return "Error: No media profiles found on camera."

                token = profiles[0].token
                uri_request = media_service.create_type('GetStreamUri')
                uri_request.ProfileToken = token
                uri_request.StreamSetup = {'Stream': 'RTP-Unicast', 'Transport': {'Protocol': 'RTSP'}}
                
                uri_response = await resolve_awaitable(media_service.GetStreamUri(uri_request))
                stream_uri = uri_response.Uri

                if ONVIF_USER and ONVIF_PASS:
                    parts = stream_uri.split('://')
                    stream_uri = f"{parts[0]}://{ONVIF_USER}:{ONVIF_PASS}@{parts[1]}"

                cap = cv2.VideoCapture(stream_uri)
                if not cap.isOpened():
                    return "Error: Could not open camera stream with OpenCV."

                ret, frame = cap.read()
                cap.release()

                if not ret:
                    return "Error: Failed to read a frame from the camera stream."

                _, buffer = cv2.imencode('.png', frame)
                img_base64 = base64.b64encode(buffer).decode('utf-8')

                return [ImageContent(type="image", mimeType="image/png", data=img_base64)]

            # --- Other camera commands ---
            devicemgmt = await resolve_awaitable(mycam.create_devicemgmt_service())
            if not devicemgmt:
                 return "Error: Could not create a connection to the camera's management service."

            if req.command in ["reboot", "turn_on", "turn_off"]:
                await resolve_awaitable(devicemgmt.SystemReboot())
                return "Success! The camera is now rebooting."
            elif req.command == "get_status":
                info = await resolve_awaitable(devicemgmt.GetDeviceInformation())
                return f"Success! Camera is online. Model: {info.Model}, Firmware: {info.FirmwareVersion}."
            else:
                return f"Error: The command '{req.command}' is not supported for the camera."
        
        except asyncio.TimeoutError:
            return f"Error: Connection timed out to camera at {CAMERA_IP}."
        except Exception as e:
            if "401" in str(e) or "Unauthorized" in str(e): return "Error: Camera authentication failed. Please check credentials."
            # The next line is changed to use the new datetime function
            print(f"UNEXPECTED CAMERA ERROR: {e}")
            return f"An unexpected camera error occurred: {e}"

    raise McpError(ErrorData(code=INVALID_PARAMS, message=f"Unsupported command '{req.command}' for device type '{device.type}'"))

# --- Plain-text entrypoint ---
@mcp.tool(description="Accept plain text smart-home commands (e.g., 'turn on desk lamp').")
async def smart_home_text_command(
    command_text: Annotated[str, Field(description="Plain-language command like 'turn on desk lamp'")]
) -> Union[str, list[ImageContent]]:
    parsed = parse_smart_command(command_text)
    if not parsed:
        return "Sorry — I couldn't parse that. Try: 'turn on desk lamp' or 'set thermostat to 24'."

    if not parsed["device_id"]:
        return "Device not found in your device list. Run 'smart_home_discover' to see device names you can use."

    req = SmartCommandRequest(
        device_id=parsed["device_id"],
        command=parsed["command"],
        params=parsed["params"] or {},
    )
    return await smart_home_execute.fn(req)

# --- Add device helper ---
@mcp.tool(description="Add a mock smart device (demo helper).")
async def smart_home_add_device(
    id: Annotated[str, Field(description="Unique device id e.g. dev-xyz")],
    name: Annotated[str, Field(description="Human friendly name")],
    aliases: Annotated[list[str] | None, Field(description="List of searchable aliases")] = None,
    type: Annotated[str, Field(description="Device type, e.g., 'light' or 'thermostat'")] = "light",
) -> str:
    if id in _SMART_HOME_DEVICE_STORE:
        raise McpError(ErrorData(code=INVALID_PARAMS, message="Device id already exists"))
    dev = SmartDevice(id=id, name=name, aliases=aliases or [], type=type, capabilities=["on_off"] if type != "thermostat" else ["set_temperature"])
    _SMART_HOME_DEVICE_STORE[id] = dev
    return f"Added device {id} | {name}"

# --- Run MCP Server ---
async def main():
    print("🚀 Starting MCP server on http://0.0.0.0:8086")
    await mcp.run_async("streamable-http", host="0.0.0.0", port=8086)

if __name__ == "__main__":
    asyncio.run(main())
