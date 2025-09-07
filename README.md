
# Puch Home: Smart Home Control MCP Server

> Puch Home is a next-generation smart home control model context protocol server that brings simplicity, speed, and intelligence to your home automation. By leveraging Puch AI, it can enable seamless, vendor-agnostic control of your smart devices from a single, unified interface.

- **Unified Control:** Manage all your smart home devices, regardless of the brand, from one place.
- **Natural Language Commands:** Use simple sentences to control your home through any messaging app connected to Puch AI.
- **Instant & Remote Access:** No more slow, clunky vendor apps. Get instant feedback and control whether you're at home or away.
- **AI-Powered:** Built on the Puch AI and Model Context Protocol (MCP) for a truly intelligent and responsive experience.

## Demo

![](/assets/demo.gif)


## Table of Contents

1. [Tech Stack and Prerequisites](#1-tech-stack-and-prerequisites)
2. [How to Install and Run the Project](#2-how-to-install-and-run-the-project)
3. [How to Use the Project](#3-how-to-use-the-project)
4. [Future Improvements](#4-future-improvements)
5. [Acknowledgements](#5-acknowledgements)
6. [License](#6-license)

## 1. Tech Stack and Prerequisites

**Frontend:** WhatsApp (Puch AI)\
**Backend:** Python\
**Prerequisites:** Python 3.x, Git, ngrok


## 2. How to Install and Run the Project

**1. Clone the Repository:**
```
git clone https://github.com/aursalan/puch-home.git
cd puch-home
```

**2. Create and activate a Python virtual environment:**
```
# For macOS/Linux
python -m venv .venv
source .venv/bin/activate

# For Windows
python -m venv .venv
.venv\Scripts\activate
```

**3. Configure environment variables:**
- Copy the example environment file and edit it with your specific details (e.g., device credentials, authentication token).
```
cp eg.env .env
```

**4. Install dependencies:**
```
pip install -r requirements.txt
```

**5. Start the application:**
```
python main.py
```

**6. Expose your local server:**
- Use ngrok to create a public URL for your local server. This allows Puch AI to communicate with it from anywhere.
```
ngrok http 8000
```

**7. Connect Puch AI to your server:**
- In your Puch AI [chat](https://puch.ai/hi), send the following command, replacing the placeholders with your ngrok URL and the token you set in your .env file.
```
/mcp connect <YOUR_NGROK_URL>/mcp <YOUR_TOKEN>
```

## 3. How to Use the Project

Once the server is running and connected to Puch AI, you can start controlling your smart home devices by sending messages.

- **Send Commands:** Use natural language to interact with your devices.
    - "Turn on the living room light."
    - "Set the bedroom thermostat to 22 degrees."
    - "Show me a snapshot from the front door camera."

- **Test with Demo Data:** The project includes demo data, allowing you to test commands and interactions without connecting real devices.

##  4. Future Improvements

- Support for a wider range of smart device brands and types (e.g., smart locks, blinds, speakers).
- Creation of automated routines and scenes (e.g., a "Good Morning" scene that turns on lights and adjusts the thermostat).
- Proactive AI suggestions based on user habits and contextual triggers.

## 5. Acknowledgements

 - [Official Puch AI MCP Documentation](https://puch.ai/mcp)

## 6. License
This project is licensed under the [Apache-2.0](LICENSE) License.
