#!/usr/bin/env python3
"""
Telegram AI Contextual Assistant & Explainer (Userbot)
Powered by Google Gemini and Telethon.

Analyzes chat context (up to 100 messages), tracks deadlines, distinguishes
self-replies from other users, provides direct factual answers or ready-made
reply suggestions, and supports silent private delivery to Saved Messages.
"""

import os
import sys
import json
import time
import socket
import datetime
import requests
from telethon import TelegramClient, events

# Ensure UTF-8 output across environments
if sys.stdout.encoding != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(BASE_DIR, "config.json")
SESSION_NAME = os.path.join(BASE_DIR, "user_session")


def load_config():
    """Load configuration from config.json."""
    if not os.path.exists(CONFIG_PATH):
        print(f"[!] Error: {CONFIG_PATH} not found. Please run 'python login.py' first.")
        sys.exit(1)
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def get_proxies():
    """Detect if a local proxy (e.g., Happ/v2ray on 127.0.0.1:10809) is running."""
    try:
        s = socket.create_connection(("127.0.0.1", 10809), timeout=0.2)
        s.close()
        return {"http": "http://127.0.0.1:10809", "https": "http://127.0.0.1:10809"}
    except Exception:
        return None


def build_system_prompt(user_name):
    """Build dynamic system prompt personalized for the authorized user."""
    return f"""You are a personal AI assistant for {user_name} inside Telegram.
You have access to recent chat history (up to 100 messages), the exact current date/time, and {user_name}'s request.

IN THE CHAT HISTORY:
- Each message is timestamped: [YYYY-MM-DD HH:MM | relative time ago].
- Senders are explicitly labeled: [{user_name} (you)] or [Interlocutor_Name].
- Current date and time are provided in the system context header.

STRICT BEHAVIORAL RULES:

1. LANGUAGE MATCHING:
   - Always respond in the language used in the current conversation or query (if the chat is in Russian, respond in Russian; if in English, respond in English).

2. TIME TRACKING & DEADLINES:
   - Always compare commitment and promise dates with the CURRENT DATE & TIME.
   - If a promised deadline has passed (e.g., promised 'by tomorrow 3 PM' 2 days ago), explicitly note that it is expired/overdue.
   - Check subsequent messages: if {user_name} fulfilled the promise (sent files, wrote 'done', or received thanks), mark it as completed.
   - If the deadline is in the future, specify that it is active and how much time remains.

3. AUTHOR RECOGNITION (SELF VS. OTHERS):
   - If {user_name} replies to THEIR OWN past message, they are referring to what they wrote themselves. Never refer to {user_name} as 'the other person' or 'interlocutor'.
   - If {user_name} asks 'how to reply' on their own message, suggest ways to expand, clarify, or follow up on their thought.

4. LOCAL CHAT CONTEXT OVER GENERIC DICTIONARY:
   - When asked about a specific word, location, slang, or concept, FIRST look at how it was used in recent chat history.
   - Never provide a generic encyclopedia definition if the term has a specific local, personal, or conversational meaning in the chat.

5. SUGGESTED REPLIES (ONLY WHEN EXPLICITLY REQUESTED):
   - Generate ready-made reply options in quotation marks ONLY if {user_name} explicitly asks 'how to reply', 'how to answer', 'what to write', or similar ('как ответить', 'че написать').
   - If not explicitly requested, NEVER output options in quotes.

6. DIRECT ANSWERS WITHOUT META-COMMENTARY:
   - Never output meta-commentary like 'The interlocutor asked a question to test...' or 'The dialogue is proceeding in a calm manner'.
   - If the replied message is a factual question or request for information, directly provide the accurate factual answer in 1-2 concise sentences.

7. TONE & FORMATTING:
   - Strictly 2-3 concise, informative sentences. No filler words, greetings, or sign-offs.
   - Zero emojis and zero smileys.
   - No boilerplate section headers (do not write 'Summary:', 'Context:', 'Answer:').
   - Intelligent, calm, and direct conversational tone."""


def query_gemini_smart(current_time_str, chat_history_lines, user_name, replied_text=None, replied_author=None, user_query=None):
    """Query Gemini models with context, timestamps, and smart intent routing."""
    cfg = load_config()
    key = cfg.get("gemini_api_key", "").strip()
    model = cfg.get("gemini_model", "gemini-3.5-flash-lite")
    proxies = get_proxies()

    system_instruction = build_system_prompt(user_name)

    prompt_content = f"CURRENT DATE & TIME: {current_time_str}\n\n"
    if chat_history_lines:
        prompt_content += "CHAT HISTORY (CHRONOLOGICAL ORDER):\n"
        for line in chat_history_lines:
            prompt_content += f"{line}\n"
        prompt_content += "\n"

    if replied_text:
        author_str = f" from {replied_author}" if replied_author else ""
        prompt_content += f"TARGET MESSAGE REFERENCED BY {user_name.upper()}{author_str}:\n«{replied_text}»\n\n"

    if user_query:
        prompt_content += f"REQUEST / QUERY FROM {user_name.upper()}:\n{user_query}\n"
    else:
        prompt_content += (
            f"REQUEST FROM {user_name.upper()}: Executed default .ai command on the referenced message.\n"
            "Action guidelines:\n"
            "1. If the message contains a direct factual question or riddle (e.g. height, price, date, definition): directly provide the accurate factual answer (1-2 sentences). Do not explain user motives.\n"
            "2. If the message contains unfamiliar slang, jargon, or local term: concisely explain its meaning based on chat context.\n"
            "3. If the message contains hidden subtext, sarcasm, or ambiguity: clarify its intended meaning.\n"
        )

    models_to_try = [model, "gemini-3.1-flash-lite-preview", "gemini-flash-lite-latest"]

    payload = {
        "system_instruction": {"parts": [{"text": system_instruction}]},
        "contents": [{"role": "user", "parts": [{"text": prompt_content}]}],
        "generationConfig": {
            "temperature": 0.25,
            "maxOutputTokens": 250,
        },
    }

    for m in models_to_try:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{m}:generateContent?key={key}"
        for _ in range(2):
            try:
                res = requests.post(url, json=payload, proxies=proxies, timeout=12)
                if res.status_code == 200:
                    candidates = res.json().get("candidates", [])
                    if candidates:
                        return candidates[0]["content"]["parts"][0]["text"].strip()
                elif res.status_code == 429:
                    time.sleep(1)
                    continue
                else:
                    print(f"[Gemini {m} HTTP {res.status_code}]: {res.text[:120]}")
            except Exception as e:
                print(f"[Gemini {m} Exception]: {e}")
                continue

    return "Failed to connect to AI service. Please check your API key or network connection."


config = load_config()
API_ID = int(config["api_id"])
API_HASH = config["api_hash"]

client = TelegramClient(SESSION_NAME, API_ID, API_HASH)


@client.on(events.NewMessage(outgoing=True))
async def handle_user_command(event):
    """Handle .ai triggers with context awareness and private routing."""
    raw = (event.raw_text or "").strip()
    if not (raw.startswith(".ai") or raw.startswith("!ai")):
        return

    me = await client.get_me()
    user_name = me.first_name or "User"
    is_saved = event.is_private and event.chat_id == me.id

    parts = raw.split()
    first_arg = parts[1].lower() if len(parts) > 1 else ""

    # Check for private mode: .ai priv or .ai on priv
    is_private_mode = False
    if first_arg in ["priv", "private", "личка"]:
        is_private_mode = True
    elif len(parts) > 2 and parts[1].lower() == "on" and parts[2].lower() in ["priv", "private", "личка"]:
        is_private_mode = True

    # Strip command trigger
    clean_query = raw
    prefixes_to_strip = [
        ".ai on priv", ".ai on private", ".ai on pub",
        ".ai priv", ".ai private", ".ai pub",
        ".ai on", ".ai", "!ai"
    ]
    for p in prefixes_to_strip:
        if clean_query.lower().startswith(p):
            clean_query = clean_query[len(p):].strip()
            break

    # Built-in commands: help / status
    if clean_query.lower() in ["help", "помощь"]:
        help_msg = (
            "🤖 **Telegram AI Assistant (Commands):**\n\n"
            "• `.ai <question>` — ask anything (chat context or general knowledge). Edits your message with the answer.\n"
            "• Reply `.ai` or `.ai on` to any message — AI explains its meaning or answers the question directly.\n"
            "• Reply `.ai how to reply` — provides 2 suggested reply options tailored to the conversation.\n"
            "• Append `priv` (e.g. `.ai priv <question>`) — secretly sends the answer to Saved Messages.\n"
            "• `.ai status` — check model and server status."
        )
        await event.edit(help_msg)
        return

    if clean_query.lower() in ["status", "статус"]:
        cfg = load_config()
        status_msg = (
            f"📊 **AI Assistant Status:**\n"
            f"• Model: `{cfg.get('gemini_model', 'gemini-3.5-flash-lite')}`\n"
            f"• Context: up to 100 recent messages with timestamps\n"
            f"• Time Tracker: Active\n"
            f"• Status: Operational"
        )
        await event.edit(status_msg)
        return

    # Handle replied message target
    replied_text = None
    replied_author = None
    if event.is_reply:
        reply_msg = await event.get_reply_message()
        if reply_msg and reply_msg.text:
            replied_text = reply_msg.text.strip()
            if reply_msg.sender_id == me.id or reply_msg.out:
                replied_author = f"{user_name} (you, your own past message)"
            else:
                first_name = reply_msg.sender.first_name if reply_msg.sender else "Interlocutor"
                username = f" (@{reply_msg.sender.username})" if reply_msg.sender and reply_msg.sender.username else ""
                replied_author = f"{first_name}{username}"

    # Localized timestamp
    now = datetime.datetime.now(datetime.timezone.utc).astimezone()
    now_str = now.strftime("%Y-%m-%d %H:%M, %A")

    # Fetch up to 100 history messages with relative time tags
    history_lines = []
    try:
        cfg = load_config()
        limit_count = cfg.get("max_history_messages", 100)
        async for m in client.iter_messages(event.chat_id, limit=limit_count):
            if m.text and not m.text.startswith(".ai") and not m.text.startswith("!ai"):
                m_date = m.date.astimezone()
                diff = now - m_date
                if diff.total_seconds() < 3600:
                    rel = f"{max(1, int(diff.total_seconds() // 60))}m ago"
                elif diff.total_seconds() < 86400:
                    rel = f"{int(diff.total_seconds() // 3600)}h ago"
                elif diff.days == 1:
                    rel = "yesterday"
                else:
                    rel = f"{diff.days}d ago"

                time_tag = f"[{m_date.strftime('%Y-%m-%d %H:%M')} | {rel}]"

                if m.sender_id == me.id or m.out:
                    s_name = f"{user_name} (you)"
                elif m.sender:
                    s_name = m.sender.first_name or "Interlocutor"
                else:
                    s_name = "Interlocutor"
                history_lines.append(f"{time_tag} [{s_name}]: {m.text.strip()}")
        history_lines.reverse()
    except Exception as e:
        print(f"[Context fetch error]: {e}")

    chat = await event.get_chat()
    chat_title = getattr(chat, "title", None) or getattr(chat, "first_name", None) or "Direct Messages"
    print(f"\n[🔍 AI Request]: '{clean_query or 'message breakdown'}' in '{chat_title}' ({len(history_lines)} msgs context, {now_str})")

    # Generate answer from Gemini
    ans = query_gemini_smart(
        current_time_str=now_str,
        chat_history_lines=history_lines,
        user_name=user_name,
        replied_text=replied_text,
        replied_author=replied_author,
        user_query=clean_query,
    )

    if is_private_mode and not is_saved:
        # Delete trigger in chat, route response to Saved Messages
        await event.delete()
        quote_part = f"> {replied_text[:200]}...\n\n" if replied_text else ""
        card = f"📍 *Chat:* `{chat_title}`\n\n{quote_part}{ans}"
        await client.send_message("me", card)
        print(" -> [Delivered privately to Saved Messages]")
    else:
        # Edit message in place in the current chat
        await event.edit(ans)
        print(" -> [Edited in-place in current chat]")


async def main():
    cfg = load_config()
    print("=" * 65)
    print("🚀 Telegram AI Contextual Assistant (100 msgs memory)")
    print(f"• Model: {cfg.get('gemini_model', 'gemini-3.5-flash-lite')}")
    print("• Timestamp & Deadline Tracker: ACTIVE")
    print("• Self vs. Interlocutor Distinction: ACTIVE")
    print("• Default Mode: In-chat message edit")
    print("• Private Mode: Use '.ai priv' to route to Saved Messages")
    print("=" * 65)

    await client.connect()
    if not await client.is_user_authorized():
        print("\n[!] Error: Session not authorized. Run 'python login.py' first.")
        return

    me = await client.get_me()
    print(f"\n[✅ SUCCESS] Logged in as: {me.first_name} (@{me.username or me.id})")
    print("AI Userbot is online and listening for .ai commands.\n")
    await client.run_until_disconnected()


if __name__ == "__main__":
    client.loop.run_until_complete(main())
