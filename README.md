# Telegram AI Explainer & Copilot Userbot ⚡

A smart, contextual Telegram userbot powered by **Google Gemini** and **Telethon**. It seamlessly analyzes chat history (up to 100 messages), tracks commitments and deadlines, distinguishes self-messages from other speakers, explains ambiguous text or slang, and generates ready-made reply suggestions directly inside your Telegram account.

---

## ✨ Features

- **🧠 Deep Chat Context:** Fetches up to 100 recent messages with precise timestamps and relative time tags (`[2026-10-27 12:45 | 15m ago]`).
- **⏱️ Time & Deadline Tracking:** Matches promises and deadlines against real-world clock time. Instantly recognizes whether a commitment is pending, fulfilled, or overdue.
- **👤 Smart Author Attribution:** Knows when you are replying to your own past message versus someone else's.
- **💬 Ready-to-Send Reply Suggestions:** Reply with `.ai how to reply` to get 2 tailored, ready-made response suggestions.
- **🔍 Local Meaning over Dictionary:** Understands conversational slang, inside jokes, and local references from chat history rather than giving generic Wikipedia definitions.
- **🤫 Silent Private Delivery:** Append `priv` (e.g. `.ai priv what did I promise?`) to secretly delete your command and route the AI answer to your personal **Saved Messages**.
- **🚫 Zero Fluff / No Emojis:** Strictly concise (2–3 sentences), intelligent tone with no robotic boilerplate headers (`Summary:`, `Context:`) and no emojis.
- **📱 QR Code Authentication:** Log in without SMS verification codes using Telegram's native QR code scanner.

---

## 📋 Prerequisites

1. **Telegram API Credentials (`api_id` and `api_hash`):**
   - Go to [my.telegram.org](https://my.telegram.org) and log in with your phone number.
   - Navigate to **API development tools**.
   - Create a new application (e.g., app name: `TelegramAIExplainer`) to obtain your numeric `api_id` and string `api_hash`.

2. **Google Gemini API Key:**
   - Go to [Google AI Studio](https://aistudio.google.com/) and create a free API key.

3. **Python 3.10+** installed on your machine or VPS.

---

## 🚀 Quick Start

### 1. Clone the repository
```bash
git clone https://github.com/<your-username>/telegram-ai-explainer.git
cd telegram-ai-explainer
```

### 2. Install dependencies
```bash
python -m venv venv
# On Linux/macOS:
source venv/bin/activate
# On Windows:
venv\Scripts\activate

pip install -r requirements.txt
```

### 3. Run interactive setup & QR login
```bash
python login.py
```
- The setup will prompt you for your `api_id`, `api_hash`, and `gemini_api_key`, automatically creating `config.json`.
- A QR code will appear in your terminal (and open as an image).
- Open **Telegram on your phone** -> **Settings** -> **Devices** -> **Link Desktop Device** and scan the code.
- If you have 2FA (Cloud Password) enabled, enter your password when prompted.

### 4. Start the Userbot
```bash
python userbot.py
```

---

## 🕹️ Available Commands

| Command | Action | Output Location |
| :--- | :--- | :--- |
| `.ai <question>` | Ask any general question or question about recent chat messages | Current Chat (in-place edit) |
| Reply `.ai` or `.ai on` | Explains the meaning, subtext, or factual answer of the target message | Current Chat (in-place edit) |
| Reply `.ai how to reply` | Generates 2 natural, context-aware reply options | Current Chat (in-place edit) |
| `.ai priv <question>` | Secret mode: evaluates question/context privately | Saved Messages (deletes trigger from chat) |
| Reply `.ai on priv` | Secretly explains the replied message | Saved Messages (deletes trigger from chat) |
| `.ai help` | Displays the help manual | Current Chat |
| `.ai status` | Displays model status and uptime info | Current Chat |

*(Commands work with both English and Russian triggers like `.ai как ответить`, `.ai личка`).*

---

## 🖥️ 24/7 Hosting on Linux VPS (Systemd)

To keep your assistant running 24/7 on a Linux server:

1. Copy the project folder to your server:
   ```bash
   scp -r telegram-ai-explainer user@your-server-ip:~/telegram_ai
   ```

2. SSH into your server:
   ```bash
   ssh user@your-server-ip
   cd ~/telegram_ai
   chmod +x start.sh
   ```

3. Enable the user-level systemd service:
   ```bash
   mkdir -p ~/.config/systemd/user
   cp telegram-ai.service ~/.config/systemd/user/
   systemctl --user daemon-reload
   systemctl --user enable telegram-ai
   systemctl --user start telegram-ai
   ```

4. Check the status:
   ```bash
   systemctl --user status telegram-ai
   ```

---

## 🔒 Security & Privacy

- **Your credentials stay 100% on your machine:** Your Telegram session (`user_session.session`) and `config.json` are listed in `.gitignore` and are **never** committed or transmitted anywhere except official Telegram and Google Gemini endpoints.
- **Never share or commit `*.session` files:** Session files grant direct access to your Telegram account.

---

## 📄 License

This project is licensed under the [MIT License](LICENSE).
