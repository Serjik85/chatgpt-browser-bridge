# ChatGPT Browser Bridge

![Python](https://img.shields.io/badge/python-3.10+-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-API-green)
![Playwright](https://img.shields.io/badge/Playwright-browser%20automation-orange)
![Raspberry Pi](https://img.shields.io/badge/Raspberry%20Pi-supported-red)
![License](https://img.shields.io/badge/license-MIT-lightgrey)

A lightweight local HTTP bridge that allows tools like **OpenClaw**, scripts, or local AI agents to send prompts to a **logged-in ChatGPT browser session**.

No OpenAI API key required.

This project connects local software to ChatGPT through an existing browser session.

```
Client → FastAPI Proxy → Playwright → Chromium Remote Debugging → ChatGPT Web UI
```

---

# Why this exists

Many local AI tools require an **OpenAI API key**.

Sometimes you just want to experiment with:

* local agents
* Raspberry Pi setups
* home automation
* scripting
* prototypes

This bridge allows you to connect those tools to a **normal ChatGPT browser session**.

---

# Features

* Works with an existing ChatGPT browser session
* No API key required
* Runs on Raspberry Pi
* OpenAI-compatible API endpoint
* Simple chat endpoint
* systemd services included
* Chromium watchdog auto-restart
* Designed for local AI agent experimentation

---

# Architecture

```
            ┌───────────────┐
            │    Client     │
            │ OpenClaw etc. │
            └───────┬───────┘
                    │
                    ▼
           ┌─────────────────┐
           │   FastAPI API   │
           │  chatgpt_proxy  │
           └────────┬────────┘
                    │
                    ▼
            ┌─────────────┐
            │ Playwright  │
            │ automation  │
            └──────┬──────┘
                   │
                   ▼
        ┌─────────────────────┐
        │ Chromium Debug Port │
        │       :9222         │
        └─────────┬───────────┘
                  │
                  ▼
             ChatGPT Web
```

---

# Endpoints

## Simple Chat Mode

For quick testing and scripts.

```
POST /chat
```

Example:

```
curl -X POST http://127.0.0.1:8080/chat \
-H "Content-Type: application/json" \
-d '{"message":"Hello"}'
```

Response

```
{
  "response": "Hello! How can I help you?"
}
```

---

## OpenAI Compatible Mode

Used by tools like **OpenClaw**.

```
POST /v1/chat/completions
```

Example:

```
curl http://127.0.0.1:8080/v1/chat/completions \
-H "Content-Type: application/json" \
-d '{
"model":"chatgpt",
"messages":[
{"role":"user","content":"Hello"}
]
}'
```

---

# Requirements

* Raspberry Pi OS or Linux
* Python 3.10+
* Chromium
* Logged-in ChatGPT session
* Desktop environment

---

# Installation

## 1 Install dependencies

```
sudo apt update
sudo apt install -y python3 python3-pip python3-venv chromium curl
```

---

## 2 Create project folder

```
mkdir -p ~/chatgpt-bridge
cd ~/chatgpt-bridge
```

---

## 3 Create virtual environment

```
python3 -m venv .venv
source .venv/bin/activate
```

---

## 4 Install Python dependencies

```
pip install fastapi uvicorn playwright
python -m playwright install chromium
```

---

## 5 Start Chromium with debugging

```
chromium --remote-debugging-port=9222 https://chatgpt.com
```

Log into ChatGPT and keep the session open.

---

## 6 Start the proxy

```
uvicorn chatgpt_proxy:app --host 0.0.0.0 --port 8080
```

---

# Health Check

```
curl http://127.0.0.1:8080/health
```

Expected result

```
{
 "ok": true,
 "page_url": "https://chatgpt.com/"
}
```

---

# systemd Service

Install the service

```
sudo cp systemd/chatgpt-proxy.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable chatgpt-proxy
sudo systemctl start chatgpt-proxy
```

View logs

```
journalctl -u chatgpt-proxy -f
```

---

# Chromium Watchdog

Ensures Chromium remote debugging stays alive.

Install services

```
sudo cp systemd/chromium-watchdog.* /etc/systemd/system/
sudo systemctl daemon-reload
```

Enable timer

```
sudo systemctl enable chromium-watchdog.timer
sudo systemctl start chromium-watchdog.timer
```

---

# OpenClaw Configuration

Set API base to

```
http://127.0.0.1:8080/v1
```

Model name

```
chatgpt
```

---

# Debugging

Proxy logs

```
journalctl -u chatgpt-proxy -f
```

Last OpenClaw payload

```
cat ~/chatgpt-bridge/last_openclaw_payload.json
```

Health check

```
curl http://127.0.0.1:8080/health
```

---

# Limitations

This bridge intentionally forwards **only the last user message** to ChatGPT.

Agent metadata, system prompts and tools are ignored for stability.

This project is meant for **experimentation and local usage**, not production systems.

---

# Contributing

Pull requests are welcome.

Ideas for improvements:

* streaming responses
* multi-session support
* Docker image
* queue system
* agent tool forwarding

---

# License

MIT License
