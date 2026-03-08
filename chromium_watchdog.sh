#!/usr/bin/env bash
set -euo pipefail

if curl -fsS http://127.0.0.1:9222/json/version >/dev/null 2>&1; then
  exit 0
fi

pkill -f "chromium.*remote-debugging-port=9222" || true
sleep 2

export DISPLAY=:0
export XAUTHORITY=/home/serhii/.Xauthority

nohup chromium --remote-debugging-port=9222 https://chatgpt.com >/home/serhii/chatgpt-bridge/chromium-watchdog.log 2>&1 &
