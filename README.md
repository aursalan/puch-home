# 🏡 Puch Home: Smart Home Control Server

Puch Home is a next-generation smart home control server that brings simplicity, speed, and true intelligence to your home automation experience. By leveraging Puch AI and the Model Context Protocol (MCP), it enables seamless, vendor-agnostic control of your smart devices—all from a unified interface.

No more waiting for slow apps or switching vendor platforms. Puch Home is built for real convenience: one interface, one sentence, full control. Whether you're at home or away, you can manage your smart devices and receive instant feedback—all with powerful AI integration and a seamless user experience.

---

## Table of Contents

- [Project Description](#project-description)
- [Installation & Running](#installation--running)
- [Usage](#usage)
- [Acknowledgements](#acknowledgements)
- [License](#license)

---

## Project Description

Puch Home connects your smart home devices and lets you control them using natural language, via Puch AI. It supports various device types and integrates with your preferred messaging platform.

---

## Installation & Running

Follow these steps to get started:

### 1. Clone the repository

```bash
git clone https://github.com/aursalan/puch-home.git
cd puch-home
```

### 2. Create and activate a Python virtual environment

```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

### 3. Set up environment variables

- Copy the example environment file and edit your configuration:

  ```bash
  cp eg.env .env
  ```

- Open `.env` in your favorite editor, and **change the numbers and authentication variables** as needed for your setup.

### 4. Install dependencies

```bash
pip install -r requirements.txt
```

### 5. Run the application

```bash
python main.py
```

### 6. Expose your local server (optional, recommended for remote use)

Use [ngrok](https://ngrok.com/) to expose your server:

```bash
ngrok http 8000
```
*(Replace `8000` with your server's port if different.)*

### 7. Connect with Puch AI

In your Puch AI chat, run:

```
/mcp connect <NGROK_URL/mcp> <TOKEN>
```
Replace `<NGROK_URL/mcp>` with your public ngrok URL (e.g. `https://abcd1234.ngrok.io/mcp`) and `<TOKEN>` with your authentication token.

---

## Usage

- After setup, use Puch AI (e.g., through WhatsApp) to send commands to your smart home.
- You can control devices with natural language and request camera snapshots.
- For real device integration, ensure correct settings in your `.env` file.
- Demo data is available for testing most device actions.

---

## Acknowledgements

- [Official Puch AI MCP Documentation](https://puch.ai/mcp)
- [JSON-RPC 2.0 Spec](https://www.jsonrpc.org/specification)

---

## License

This project is licensed under the [MIT](LICENSE) License.
