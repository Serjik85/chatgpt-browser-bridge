# ChatGPT Browser Bridge

A lightweight local HTTP bridge that allows tools like **OpenClaw**, scripts, or local agents to send prompts to a **logged-in ChatGPT browser session**.

No OpenAI API key required.

This project connects:

Client → FastAPI Proxy → Playwright → Chromium Remote Debugging → ChatGPT

---

# Features

- Uses an existing ChatGPT browser session
- No OpenAI API key required
- Works on Raspberry Pi
- OpenAI compatible endpoint
- Simple chat endpoint
- Chromium watchdog auto-restart
- systemd services included

---

# Architecture
Client
↓
HTTP API (FastAPI)
↓
Playwright
↓
Chromium remote debugging
↓
ChatGPT web UI
---

# Endpoints
POST /chat
Example:

curl -X POST http://127.0.0.1:8080/chat

-H "Content-Type: application/json"
-d '{"message":"Hello"}'

POST /v1/chat/completions

curl http://127.0.0.1:8080/v1/chat/completions

-H "Content-Type: application/json"
-d '{
"model":"chatgpt",
"messages":[
{"role":"user","content":"Hello"}
]
}'

---

# Requirements

- Raspberry Pi OS or Linux
- Python 3.10+
- Chromium
- Logged-in ChatGPT session
- Desktop environment

---

# Installation
sudo apt update
sudo apt install python3 python3-pip python3-venv chromium

python3 -m venv .venv
source .venv/bin/activate
pip install fastapi uvicorn playwright
python -m playwright install chromium

### Start Chromium
chromium --remote-debugging-port=9222 https://chatgpt.com

Login to ChatGPT.

---

### Start proxy
uvicorn chatgpt_proxy:app --host 0.0.0.0 --port 8080

---

# Health check

curl http://127.0.0.1:8080/health
---

# systemd service


sudo cp systemd/chatgpt-proxy.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable chatgpt-proxy
sudo systemctl start chatgpt-proxy

---

# Chromium watchdog

Ensures Chromium remote debugging stays alive.


sudo cp systemd/chromium-watchdog.* /etc/systemd/system/
sudo systemctl enable chromium-watchdog.timer
sudo systemctl start chromium-watchdog.timer

---

# OpenClaw configuration

API base:
http://127.0.0.1:8080/v1

Model:
chatgpt
---

# Limitations

This bridge intentionally forwards **only the last user message** to ChatGPT.

Agent metadata, tools, and system prompts are ignored for stability.

---

# Debugging
Proxy logs
journalctl -u chatgpt-proxy -f

Last OpenClaw payload
cat ~/chatgpt-bridge/last_openclaw_payload.json
---

# Why this project exists

Many local AI tools require an OpenAI API key.

This bridge allows experimenting with **browser-based ChatGPT sessions** using local agents and Raspberry Pi devices.

---

# License


