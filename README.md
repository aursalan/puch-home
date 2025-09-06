# 🏡 Puch Home: Smart Home Control Server — Powered by Puch AI

Welcome to **Puch Home**—the next evolution in smart home control, powered by Puch AI and Model Context Protocol (MCP)!  
No more waiting for slow apps or juggling dozens of vendor platforms. With Puch Home, you control your devices with a single sentence—anywhere, anytime.

---

## 📹 Demo

![](assets/demo.gif)

---

## ✨ What Makes Puch Home Different?

### ⚡ Instant, Flexible Smart Home Control
- Tired of waiting for apps to load just to turn off a light or fan?  
- Puch Home lets you send a single message (from WhatsApp) to control devices instantly.  
- No lag. No app installs. No limits.

### 🧠 Powered by MCP + Puch AI
- **Model Context Protocol (MCP)** safely connects your AI to real-world devices and tools.
- **Puch AI integration** means you can use natural language—no technical jargon needed.

### 🌍 Vendor-Agnostic, Always Growing
- One interface for all your smart devices (multi-vendor support coming soon).
- Turn your phone into a portable Alexa—even when you’re not home.

---

## 🚨 Real-Time Security Camera Integration (MVP Feature)

Puch Home includes a real-time snapshot feature using ONVIF and a security camera.  
- Get a live image from a security cam sent straight to your phone.
- **Note:** This is an MVP feature—currently only a pre-configured security camera is supported (due to hackathon time constraints).  
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

## Table of Contents

- [Project Description](#🏡-puch-home-smart-home-control-server--powered-by-puch-ai)
- [How to Install and Run the Project](#how-to-install-and-run-the-project)
- [How to Use the Project](#how-to-use-the-project)
- [Acknowledgements](#acknowledgements)
- [License](#license)

## How to Install and Run the Project

This project is built to run on your local machine, and was developed during a hackathon.

To run it yourself:
- Clone the repository:  
  `git clone https://github.com/aursalan/puch-home.git`
- Create and activate a virtual environment:  
  `uv venv`  
  `uv sync`  
  `source .venv/bin/activate`
- Configure the `.env` file for authentication and device settings:  
  `cp .env.example .env`  
  *Edit* `AUTH_TOKEN`, `MY_NUMBER`, camera variables in `.env`
- Start the MCP server:  
  `cd mcp-bearer-token`  
  `python mcp_starter.py`
- (Optional) Expose your server publicly with ngrok:  
  `ngrok http 8086`

**No additional setup is required for basic functionality if dependencies are installed.**

## How to Use the Project

Once the server is running:
- Connect with Puch AI via WhatsApp using the provided `/mcp connect` command.
- Control your smart home devices and request security camera snapshots in natural language.
- Demo data is used for most device actions; real camera snapshots require ONVIF configuration in `.env`.

## Acknowledgements

 - [Official Puch AI MCP Documentation](https://puch.ai/mcp)
 - [JSON-RPC 2.0 Spec](https://www.jsonrpc.org/specification)

## License
This project is licensed under the [MIT](LICENSE) License.
````
