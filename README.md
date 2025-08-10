# 🚀 Puch Home: Your Portable Smart Home AI 

Welcome to **Puch Home**—the next evolution in smart home control, powered by Puch AI and Model Context Protocol (MCP)!  
No more waiting for slow apps or juggling dozens of vendor platforms. With Puch Home, you control your devices with a single sentence—anywhere, anytime.

---

## 🌟 What Makes Puch Home Different?

### ⚡ Instant, Flexible Smart Home Control
Tired of waiting for apps to load just to turn off a light or fan?  
Puch Home lets you send a single message (from WhatsApp) to control devices instantly.  
No lag. No app installs. No limits.

### 🧠 Powered by MCP + Puch AI
- **Model Context Protocol (MCP)** safely connects your AI to real-world devices and tools.
- **Puch AI integration** means you can use natural language—no technical jargon needed.

### 🌍 Vendor-Agnostic, Always Growing
- One interface for all your smart devices (multi-vendor support coming soon).
- Turn your phone into a portable Alexa—even when you’re not home.

---

## 🚨 Real-Time Security Camera Integration (MVP Feature)

**New for Hackathon!**  
Puch Home now includes a real-time snapshot feature using ONVIF and a security camera.  
- Get a live image from a security cam sent straight to your phone.
- **Note:** This is an MVP feature—currently only a pre-configured security camera is supported (due to hackathon time constraints and lack of open IOT APIs).  
- **Future Scope:** Full support for adding/removing your own devices is planned. For now, you get a taste of real-world integration beyond just mock/demo data!

---

## ⚠️ Demo Data Notice

> **Note:**  
> The current version of Puch Home works with _demo data for most device actions_.  
> Device toggling is simulated for demonstration, **except for the real security camera snapshot (ONVIF)**.
>
> **Future Scope:**  
> The architecture is being built for true remote control, automation, and multi-device management—all from one tool.  
> Stay tuned as real device logic and multi-vendor APIs are added!

---

## 💡 Why This Project?

> This started as a personal hackathon project to solve a real pain:  
> "Why should I wait for an app to load just to turn something on or off?"  
> With Puch Home, your AI listens and acts, no matter where you are.  
> It’s your voice-powered remote for the whole smart world!

---

## 🛠️ Features

- **One-Sentence Commands:**  
  "Turn off the bedroom light", "Switch on the fan"—just say it.
- **Remote Device Control:**  
  Works over WhatsApp or Puch AI, even when away from home.
- **Security Camera Snapshots (ONVIF):**  
  Get a real photo from your security camera, instantly.
- **No Vendor Lock-In:**  
  Future-proof: control multiple brands from one place.
- **No App Overload:**  
  Ditch the clutter. One tool, every device.
- **Job Search & Image Processing Tools Included:**  
  Use built-in tools for job hunting and image editing (from the original MCP starter).

---

## 🚦 Quickstart

### 1. Clone & Set Up

```bash
git clone https://github.com/aursalan/puch-home.git
cd puch-home
uv venv
uv sync
source .venv/bin/activate
```

### 2. Configure Environment

Copy and edit your `.env` file:

```bash
cp .env.example .env
# Edit AUTH_TOKEN and MY_NUMBER in .env
```

### 3. Start the Server

```bash
cd mcp-bearer-token
python mcp_starter.py
```

You'll see: `🚀 Starting MCP server on http://0.0.0.0:8086`

### 4. Make Your Server Public

Expose your server with [ngrok](https://ngrok.com/download):

```bash
ngrok http 8086
```

---

## 🤖 Connect with Puch AI

1. **[Open Puch AI on WhatsApp](https://wa.me/+919998881729)**
2. **Send the connect command:**

   ```
   /mcp connect https://your-ngrok-url.ngrok.app/mcp your_secret_token_here
   ```

Now, you’re ready to control your home from anywhere, in natural language!

---

## 🔐 Authentication

- **Bearer token authentication** is required by Puch AI for all MCP servers.
- Your `.env` should include:
  - `AUTH_TOKEN=your_secret_token_here`
  - `MY_NUMBER=919876543210` (your WhatsApp number, with country code)

---

## 🏗️ Extend & Customize

Want to add more tools?  
Just define new tool functions with `@mcp.tool` in `mcp_starter.py`.  
For example:

```python
@mcp.tool(description="Your tool description")
async def your_tool_name(
    parameter: Annotated[str, Field(description="Parameter description")]
) -> str:
    # Your tool logic here
    return "Tool result"
```

Check the [official docs](https://puch.ai/mcp) for examples and protocol details!

---

## 📚 Documentation & Resources

### Guides & References
- [Official Puch AI MCP Documentation](https://puch.ai/mcp)
- [Join the Discord](https://discord.gg/VMCnMvYx)
- [JSON-RPC 2.0 Spec](https://www.jsonrpc.org/specification)

### Supported vs Unsupported Features

**✓ Supported:**
- Core protocol messages
- Tool definitions and calls
- Authentication (Bearer & OAuth)
- Error handling

**✗ Not Supported:**
- Videos extension
- Resources extension
- Prompts extension

---

## 🛠️ Included Tools (from MCP Starter)

### 🎯 Job Finder Tool
- **Analyze job descriptions**: Paste any job description and get smart insights
- **Fetch job postings from URLs**: Give a job posting link and get the full details
- **Search for jobs**: Use natural language to find relevant job opportunities

### 🖼️ Image Processing Tool
- **Convert images to black & white**: Upload any image and get a monochrome version

### 🛡️ Security Camera Snap (ONVIF)
- **Get a real snapshot from your security camera!**  
  (Hackathon MVP: only one preconfigured camera, but architecture supports future expansion)

---

## 🔧 Troubleshooting & Debug

- Use `/mcp diagnostics-level debug` in Puch AI to get detailed error messages.
- For server logs, check your running process console.

---

## 🚀 Build with Puch!

This project started as a hackathon experiment.  
Now, it’s your turn—fork it, remix it, and make your smart home truly smart.  
Tag your builds with **#BuildWithPuch**!

**Happy hacking!**


---
