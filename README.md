# 🏡 Puch Home: Smart Home Control Server 

Puch Home is a next-generation smart home control server that brings simplicity, speed, and true intelligence to your home automation experience. By leveraging Puch AI and the Model Context Protocol (MCP), Puch Home lets you control all your devices using natural language—just send a message from WhatsApp to toggle your lights, fans, or other smart appliances instantly.

No more waiting for slow apps or switching between different vendor platforms. Puch Home is built for real convenience: one interface, one sentence, full control. The platform is vendor-agnostic, designed for easy expansion, and provides real-time features like security camera snapshots using ONVIF.

Whether you're at home or away, you can manage your smart devices and receive instant feedback—all with powerful AI integration and a seamless user experience. Puch Home is your voice-powered remote for a truly smart home.

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
