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
import zeep.cache
zeep.cache.SqliteCache = zeep.cache.InMemoryCache

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

# --- Fetch Utility Class (unchanged) ---
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

# --- Models that were missing earlier ---
class SmartDevice(BaseModel):
    id: str
    name: str
    aliases: List[str] = []
    type: Literal["light", "thermostat", "plug", "camera"]
    online: bool = True
    capabilities: List[str] = []

class SmartCommandRequest(BaseModel):
    device_id: str
    command: str
    params: dict | None = None

# --- Smart Command Parser ---
def parse_smart_command(user_text: str) -> dict | None:
    t = user_text.lower().strip()

    # Turn On triggers
    turn_on_phrases = [
        "turn on", "switch on", "power on", "activate", "enable", "light up",
        "start", "boot up", "fire up", "initiate", "run", "begin", "wake up",
        "bring online", "turn my", "turn the", "switch my", "switch the",
        "make it on", "get it going", "launch", "kickstart", "ignite",
        "let there be light", "resume power", "switch it on", "turn this on",
        "plug in", "give power", "flip the switch", "power it up"
    ]

    # Turn Off triggers
    turn_off_phrases = [
        "turn off", "switch off", "power off", "deactivate", "disable", "shut down",
        "stop", "cut off", "turn my", "turn the", "kill", "halt", "pause", "end",
        "put to sleep", "cut the power", "switch my", "switch the", "unplug",
        "remove power", "stop running", "power it down", "turn this off", "shut the",
        "flip the switch off", "dark mode", "kill the lights"
    ]

    # Set Temperature triggers
    set_temp_phrases = [
        "set temperature", "set thermostat", "change temperature", "adjust temperature",
        "temperature to", "thermostat to", "heat to", "cool to", "make it", "set it to",
        "increase temperature", "decrease temperature", "raise temp", "lower temp",
        "set degrees", "make it warmer", "make it colder", "chill to", "warm to",
        "set climate to", "adjust climate", "set ac to", "set heater to",
        "set the room temp", "bring temp to", "temp at", "set room to"
    ]

    # Status Check triggers
    status_phrases = [
        "status", "state", "is the", "check", "show", "tell me", "report",
        "how is", "current state", "what's the", "is my", "condition of", "give me status",
        "get status", "how's the", "is it working", "is it on", "is it off",
        "show me if", "are we online", "how's it going", "update me", "what's up with"
    ]

    # Reboot triggers
    reboot_phrases = [
        "reboot", "restart", "reset", "power cycle", "reload", "re initialize",
        "refresh", "boot again", "turn it off and on", "cycle power", "re launch",
        "hard reset", "soft reset", "re kick", "system restart", "system reboot",
        "reset cam", "reset device", "reset this", "reboot this", "refresh the"
    ]

    # Take Snapshot triggers
    snapshot_phrases = [
        "snapshot", "picture", "photo", "image", "take a picture", "take photo",
        "capture", "grab image", "record still", "take snapshot", "show me the view",
        "take a shot", "snap a photo", "camera shot", "screen capture", "cam shot",
        "shoot", "snap it", "grab a frame", "freeze frame", "click a photo",
        "photograph", "take image", "see the camera", "view from", "what camera sees",
        "live view", "get me a shot", "look at camera", "show picture", "record image"
    ]

    # Detect action
    action = None
    if any(p in t for p in turn_on_phrases):
        action = "turn_on"
    elif any(p in t for p in turn_off_phrases):
        action = "turn_off"
    elif any(p in t for p in set_temp_phrases) or re.search(r"\bset .* to \d{2}\b", t):
        action = "set_temperature"
    elif any(p in t for p in status_phrases):
        action = "get_status"
    elif any(p in t for p in reboot_phrases):
        action = "reboot"
    elif any(p in t for p in snapshot_phrases):
        action = "take_snapshot"

    if not action:
        return None

    # Match device by name or alias
    device_id = None
    for dev in _SMART_HOME_DEVICE_STORE.values():
        if dev.name.lower() in t or any(alias in t for alias in dev.aliases):
            device_id = dev.id
            break

    # Extract temperature if needed
    params: dict = {}
    if action == "set_temperature":
        m = re.search(r"(\d{2})\b", t)
        if m:
            params["temperature"] = int(m.group(1))

    return {"device_id": device_id, "command": action, "params": params}


# --- In-memory device store (unchanged) ---
_SMART_HOME_DEVICE_STORE: dict[str, SmartDevice] = {
    "lamp": SmartDevice(id="lamp", name="Desk Lamp", aliases=["desk lamp", "lamp"], type="light", capabilities=["on_off"]),
    "therm": SmartDevice(id="therm", name="Living-Room Thermostat", aliases=["thermostat"], type="thermostat", capabilities=["set_temperature","on_off"]),
    "plug": SmartDevice(id="plug", name="Coffee Plug", aliases=["coffee maker"], type="plug", capabilities=["on_off"]),
    "cam": SmartDevice(id="cam", name="Security Camera", aliases=["camera", "security cam"], type="camera", capabilities=["reboot", "get_status", "take_snapshot"]),
}

# --- RichToolDescription for Smart Home Tools ---
SMART_HOME_DISCOVER_DESCRIPTION = RichToolDescription(
    description="Scan and list all connected smart home devices.",
    use_when="Use this tool when the user needs to see which devices are available and their capabilities before sending a command.",
    side_effects="None — only returns a list of devices and their details."
)

SMART_HOME_COMMAND_DESCRIPTION = RichToolDescription(
    description=(
        "Control smart home devices by sending a plain-language text command."
        "Supports lights, plugs, thermostats, and ONVIF-compatible security cameras."
    ),
    use_when="Use this when the user wants to turn devices on/off, set temperatures, check status of devices, reboot a camera, or take snapshots or pictures of camera.",
    side_effects=(
        "May change device states such as turning devices on/off, changing thermostat temperature, "
        "or rebooting a camera. Camera snapshot commands will return an image."
    )
)

SMART_HOME_ADD_DEVICE_DESCRIPTION = RichToolDescription(
    description="Add a new mock smart device into the system for testing or demonstration purposes.",
    use_when="Use this tool when you want to simulate a new smart device without using real hardware.",
    side_effects="Updates the in-memory device store, making the new device available for control."
)

# --- Discover tool ---
@mcp.tool(description=SMART_HOME_DISCOVER_DESCRIPTION.model_dump_json())
async def smart_home_discover() -> str:
    lines = ["Discovered devices:"]
    for d in _SMART_HOME_DEVICE_STORE.values():
        lines.append(f"- {d.id} | {d.name} | aliases={d.aliases} | type={d.type} | caps={d.capabilities} | online={d.online}")
    return "\n".join(lines)

# --- Unified smart home command tool (TEXT ONLY) ---
@mcp.tool(description=SMART_HOME_COMMAND_DESCRIPTION.model_dump_json())
async def smart_home_command(
    command_text: Annotated[str, Field(description="Plain-language command like 'turn on desk lamp'")]
) -> Union[str, list[ImageContent]]:
    if not command_text:
        raise McpError(ErrorData(code=INVALID_PARAMS, message="Please provide a text command."))

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

    device = _SMART_HOME_DEVICE_STORE.get(req.device_id)
    if not device:
        raise McpError(ErrorData(code=INVALID_PARAMS, message=f"Device {req.device_id} not found"))

    # --- MOCK DEVICE LOGIC ---
    if device.type in ["light", "plug", "thermostat"]:
        if req.command == "turn_on":
            return f"OK: Mock {device.name} is now ON"
        if req.command == "turn_off":
            return f"OK: Mock {device.name} is now OFF"
        if req.command == "get_status":
            return f"OK: Mock {device.name} is {'online' if device.online else 'offline'}"
        if req.command == "set_temperature":
            temp = req.params.get("temperature")
            if temp is None:
                raise McpError(ErrorData(code=INVALID_PARAMS, message="Missing temperature"))
            return f"OK: Mock {device.name} temperature set to {temp}°C"

    # --- REAL CAMERA LOGIC ---
    if device.type == "camera":
        if not all([CAMERA_IP, ONVIF_USER, ONVIF_PASS]):
            return "Error: Camera credentials are not configured on the server."

        try:
            print(f"[{datetime.datetime.now()}] DEBUG: Starting camera command '{req.command}'")
            mycam = ONVIFCamera(CAMERA_IP, ONVIF_PORT, ONVIF_USER, ONVIF_PASS)
            await resolve_awaitable(mycam.update_xaddrs())

            if req.command == "take_snapshot" OR "":
                media_service = await resolve_awaitable(mycam.create_media_service())
                profiles = await resolve_awaitable(media_service.GetProfiles())
                if not profiles:
                    return "Error: No media profiles available on camera."
                token = profiles[0].token
                uri_request = media_service.create_type('GetStreamUri')
                uri_request.ProfileToken = token
                uri_request.StreamSetup = {'Stream': 'RTP-Unicast', 'Transport': {'Protocol': 'RTSP'}}

                uri_response = await resolve_awaitable(media_service.GetStreamUri(uri_request))
                stream_uri = uri_response.Uri
                if ONVIF_USER and ONVIF_PASS:
                    # inject credentials into URI
                    parts = stream_uri.split('://', 1)
                    if len(parts) == 2:
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
                return "Error: Could not connect to the camera's management service."

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
            if "401" in str(e) or "Unauthorized" in str(e):
                return "Error: Camera authentication failed. Please check credentials."
            print(f"UNEXPECTED CAMERA ERROR: {e}")
            return f"An unexpected camera error occurred: {e}"

    raise McpError(ErrorData(code=INVALID_PARAMS, message=f"Unsupported command '{req.command}' for device type '{device.type}'"))

# --- Add device helper ---
@mcp.tool(description=SMART_HOME_ADD_DEVICE_DESCRIPTION.model_dump_json())
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
