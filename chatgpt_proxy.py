#~/chatgpt-bridge/chatgpt_proxy.py

import asyncio
import json
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from playwright.async_api import async_playwright


CDP_URL = "http://127.0.0.1:9222"
PAYLOAD_DEBUG_FILE = "/home/serhii/chatgpt-bridge/last_openclaw_payload.json"

playwright_instance = None
browser = None
page = None
request_lock = asyncio.Lock()


class ChatRequest(BaseModel):
    message: str


def log(message: str) -> None:
    print(f"[chatgpt-proxy] {message}", flush=True)


def normalize_content(content) -> str:
    if content is None:
        return ""

    if isinstance(content, str):
        return content.strip()

    if isinstance(content, list):
        parts = []
        for item in content:
            if isinstance(item, str):
                text = item.strip()
                if text:
                    parts.append(text)
            elif isinstance(item, dict):
                if item.get("type") == "text" and isinstance(item.get("text"), str):
                    text = item["text"].strip()
                    if text:
                        parts.append(text)
                elif isinstance(item.get("content"), str):
                    text = item["content"].strip()
                    if text:
                        parts.append(text)
        return "\n".join(parts).strip()

    if isinstance(content, dict):
        if isinstance(content.get("text"), str):
            return content["text"].strip()
        if isinstance(content.get("content"), str):
            return content["content"].strip()

    return str(content).strip()


def extract_last_user_message_from_payload(payload: dict) -> str:
    messages = payload.get("messages", [])

    if isinstance(messages, list):
        for message in reversed(messages):
            if not isinstance(message, dict):
                continue

            if message.get("role") != "user":
                continue

            text = normalize_content(message.get("content"))
            if text:
                return text

    input_value = payload.get("input")
    text = normalize_content(input_value)
    if text:
        return text

    prompt_value = payload.get("prompt")
    text = normalize_content(prompt_value)
    if text:
        return text

    return ""


async def get_last_assistant_message(current_page) -> str:
    nodes = current_page.locator('[data-message-author-role="assistant"]')
    count = await nodes.count()

    if count == 0:
        return ""

    last = nodes.nth(count - 1)
    parts = await last.locator("p, li, pre, code").all_inner_texts()

    cleaned = [p.strip() for p in parts if p.strip()]
    if cleaned:
        return "\n".join(cleaned)

    return (await last.inner_text()).strip()


async def wait_for_new_answer(current_page, previous_last: str, timeout_ms: int = 120000) -> str:
    await current_page.wait_for_function(
        """
        ([previousLast]) => {
            const nodes = Array.from(document.querySelectorAll('[data-message-author-role="assistant"]'));
            if (!nodes.length) return false;
            const last = nodes[nodes.length - 1];
            const text = (last.innerText || "").trim();
            return !!text && text !== previousLast;
        }
        """,
        arg=[previous_last],
        timeout=timeout_ms,
    )

    await current_page.wait_for_timeout(1500)
    return await get_last_assistant_message(current_page)


async def connect_browser():
    global playwright_instance, browser, page

    if browser is not None and page is not None:
        try:
            _ = page.url
            return
        except Exception:
            log("Existing browser/page handle is stale, reconnecting")

    if playwright_instance is not None:
        try:
            await playwright_instance.stop()
        except Exception:
            pass
        playwright_instance = None

    browser = None
    page = None

    log(f"Connecting to Chromium CDP at {CDP_URL}")
    playwright_instance = await async_playwright().start()
    browser = await playwright_instance.chromium.connect_over_cdp(CDP_URL)

    if not browser.contexts:
        raise RuntimeError("No browser contexts found in Chromium. Open Chromium with --remote-debugging-port=9222")

    context = browser.contexts[0]

    if not context.pages:
        raise RuntimeError("No open pages found in Chromium. Open chatgpt.com in Chromium first")

    page = context.pages[0]
    log(f"Connected to page: {page.url}")


async def ensure_chatgpt_ready():
    global page

    await connect_browser()

    if "chatgpt.com" not in page.url:
        log("Active page is not chatgpt.com, navigating there")
        await page.goto("https://chatgpt.com", wait_until="domcontentloaded", timeout=60000)
        await page.wait_for_timeout(3000)

    input_box = page.locator('div[role="textbox"][contenteditable="true"]').first
    await input_box.wait_for(state="visible", timeout=30000)
    return input_box


async def send_to_chatgpt(message: str) -> str:
    global page

    async with request_lock:
        started = time.time()
        safe_preview = message[:120].replace("\n", "\\n")
        log(f"Incoming prompt: {safe_preview!r}")

        try:
            input_box = await ensure_chatgpt_ready()
            previous_last = await get_last_assistant_message(page)

            await input_box.click()
            await page.keyboard.press("Control+A")
            await page.keyboard.press("Backspace")
            await page.keyboard.type(message, delay=15)
            await page.keyboard.press("Enter")

            log("Prompt sent, waiting for answer")
            answer = await wait_for_new_answer(page, previous_last)

            elapsed = time.time() - started
            answer_preview = answer[:120].replace("\n", "\\n")
            log(f"Answer received in {elapsed:.2f}s: {answer_preview!r}")
            return answer

        except Exception as e:
            log(f"ERROR while sending prompt: {e}")
            raise


@asynccontextmanager
async def lifespan(app: FastAPI):
    log("Starting ChatGPT proxy")
    try:
        await connect_browser()
    except Exception as e:
        log(f"Startup warning: {e}")
    yield
    log("Stopping ChatGPT proxy")
    try:
        if browser is not None:
            await browser.close()
    except Exception:
        pass
    try:
        if playwright_instance is not None:
            await playwright_instance.stop()
    except Exception:
        pass


app = FastAPI(lifespan=lifespan)


@app.get("/health")
async def health():
    try:
        await connect_browser()
        return {
            "ok": True,
            "page_url": page.url if page else None,
        }
    except Exception as e:
        return {
            "ok": False,
            "error": str(e),
        }


@app.post("/chat")
async def chat(req: ChatRequest):
    try:
        response = await send_to_chatgpt(req.message)
        return {"response": response}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/v1/chat/completions")
async def openai_chat(req: dict):
    try:
        with open(PAYLOAD_DEBUG_FILE, "w", encoding="utf-8") as f:
            json.dump(req, f, ensure_ascii=False, indent=2)

        user_message = extract_last_user_message_from_payload(req)

        if not user_message:
            preview = str(req)[:500].replace("\n", "\\n")
            log(f"Could not extract user message from payload: {preview}")
            raise HTTPException(status_code=400, detail="No user message provided")

        response = await send_to_chatgpt(user_message)

        return {
            "id": "chatcmpl-local",
            "object": "chat.completion",
            "choices": [
                {
                    "index": 0,
                    "message": {
                        "role": "assistant",
                        "content": response
                    },
                    "finish_reason": "stop"
                }
            ]
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
