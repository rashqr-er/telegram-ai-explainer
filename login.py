#!/usr/bin/env python3
"""
Telegram AI Assistant - Interactive Setup & QR Login
Allows users to configure API credentials and authorize Telegram via QR code (no SMS required).
"""

import os
import sys
import json
import asyncio
import qrcode
from telethon import TelegramClient, errors

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(BASE_DIR, "config.json")
CONFIG_EXAMPLE_PATH = os.path.join(BASE_DIR, "config.example.json")
SESSION_NAME = os.path.join(BASE_DIR, "user_session")


def ensure_config():
    """Ensure config.json exists or prompt user to create it interactively."""
    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                cfg = json.load(f)
                if cfg.get("api_id") and cfg.get("api_hash") and cfg.get("gemini_api_key"):
                    if cfg["api_id"] != "YOUR_TELEGRAM_API_ID":
                        return cfg
        except Exception:
            pass

    print("=" * 65)
    print("🤖 Telegram AI Assistant - Initial Configuration Setup")
    print("=" * 65)
    print("No valid config.json found. Let's configure your credentials now.\n")

    print("1. Telegram API Credentials (get free at https://my.telegram.org):")
    api_id_input = input("   Enter your API ID (numbers only): ").strip()
    api_hash_input = input("   Enter your API Hash: ").strip()

    print("\n2. Google Gemini API Key (get free at https://aistudio.google.com):")
    gemini_key_input = input("   Enter your Gemini API Key: ").strip()

    cfg = {
        "api_id": int(api_id_input),
        "api_hash": api_hash_input,
        "gemini_api_key": gemini_key_input,
        "gemini_model": "gemini-3.5-flash-lite",
        "max_history_messages": 100,
        "auto_reply_enabled": False,
    }

    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(cfg, f, indent=2, ensure_ascii=False)

    print("\n✅ Configuration saved to config.json\n")
    return cfg


async def run_qr_login(cfg):
    """Authenticate Telegram session using QR code."""
    api_id = int(cfg["api_id"])
    api_hash = cfg["api_hash"]

    client = TelegramClient(SESSION_NAME, api_id, api_hash)
    await client.connect()

    if await client.is_user_authorized():
        me = await client.get_me()
        print("=" * 65)
        print(f"✅ Already authorized as: {me.first_name} (@{me.username or me.id})")
        print("You can start the assistant directly by running:")
        print("   python userbot.py")
        print("=" * 65)
        await client.disconnect()
        return True

    print("=" * 65)
    print("📱 Telegram QR Code Authorization (No SMS required)")
    print("=" * 65)
    print("Generating authentication QR code...\n")

    qr_login = await client.qr_login()
    qr_img_path = os.path.join(BASE_DIR, "telegram_login_qr.png")
    opened_image = False

    while True:
        # Save QR code image file
        img = qrcode.make(qr_login.url)
        img.save(qr_img_path)

        # Attempt to open image in default desktop viewer on first loop
        if not opened_image:
            try:
                if sys.platform == "win32":
                    os.startfile(qr_img_path)
                elif sys.platform == "darwin":
                    os.system(f'open "{qr_img_path}"')
                opened_image = True
            except Exception:
                pass

        print("Scan the QR code below using your Telegram mobile app:")
        print("1. Open Telegram on your phone.")
        print("2. Go to: Settings -> Devices -> Link Desktop Device.")
        print("3. Point your camera at the QR code below or open 'telegram_login_qr.png'.\n")

        # Print ASCII QR code in terminal
        try:
            qr = qrcode.QRCode()
            qr.add_data(qr_login.url)
            qr.print_ascii(invert=True)
        except Exception:
            print(f"(ASCII preview unavailable. Please open: {qr_img_path})")

        print("\nWaiting for QR code scan on your phone...\n")

        try:
            user = await qr_login.wait()
            break
        except asyncio.TimeoutError:
            print("⏳ QR code expired. Refreshing new code...")
            await qr_login.recreate()
        except errors.SessionPasswordNeededError:
            print("\n🔐 Two-Step Verification (2FA) is enabled on this account.")
            password = input("Enter your 2FA cloud password: ")
            await client.sign_in(password=password)
            break

    me = await client.get_me()
    print("\n" + "=" * 65)
    print(f"🎉 Login successful! Welcome, {me.first_name} (@{me.username or me.id})")
    print(f"Session saved to: {SESSION_NAME}.session")
    print("=" * 65)
    print("\nYou can now start the assistant anytime with:")
    print("   python userbot.py\n")

    # Clean up temporary QR code image
    if os.path.exists(qr_img_path):
        try:
            os.remove(qr_img_path)
        except Exception:
            pass

    await client.disconnect()
    return True


def main():
    cfg = ensure_config()
    try:
        asyncio.run(run_qr_login(cfg))
    except KeyboardInterrupt:
        print("\n[!] Setup cancelled by user.")
    except Exception as e:
        print(f"\n[!] Error during setup: {e}")


if __name__ == "__main__":
    main()
