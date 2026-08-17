import os
import re
import threading
from datetime import timedelta
from io import BytesIO

import discord
from discord.ext import commands
from PIL import Image
import pytesseract

from fastapi import FastAPI
import uvicorn


# =========================
# CONFIG
# =========================

TOKEN = os.getenv("DISCORD_TOKEN")

SCAM_THRESHOLD = 6
TIMEOUT_MINUTES = 30
flagged_users = set()

PORT = int(os.getenv("PORT", "10000"))


# =========================
# WEB SERVER FOR RENDER
# =========================

app = FastAPI()


@app.get("/")
def home():
    return {
        "status": "online",
        "bot": "Crypto Scam Detector"
    }


def run_web_server():
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=PORT
    )


# =========================
# DISCORD
# =========================

intents = discord.Intents.default()

intents.message_content = True
intents.members = True


bot = commands.Bot(
    command_prefix="!",
    intents=intents
)


# =========================
# SCAM RULES
# =========================

RULES = {

    "free crypto": 4,
    "free bitcoin": 4,
    "free btc": 4,
    "free ethereum": 4,
    "free eth": 4,

    "crypto giveaway": 4,
    "btc giveaway": 4,
    "eth giveaway": 4,

    "cryptocurrency casino": 3,
    "crypto casino": 3,

    "claim your reward": 3,
    "claim your bonus": 3,
    "claim reward": 3,

    "activate code": 2,
    "promo code": 2,
    "special promo code": 3,

    "withdrawal successful": 2,
    "withdrawal of": 2,

    "giving away": 3,
    "giveaway": 2,

    "connect wallet": 4,
    "verify wallet": 4,
    "wallet verification": 4,

    "double your crypto": 5,
    "double your btc": 5,
    "double your eth": 5,

    "send 1 get 2": 5,

}


# =========================
# OCR
# =========================

def extract_text(image_bytes):

    image = Image.open(
        BytesIO(image_bytes)
    )

    image = image.convert("RGB")

    text = pytesseract.image_to_string(
        image
    )

    return text.lower()


# =========================
# SCAM DETECTION
# =========================

def detect_scam(text):

    score = 0
    matches = []

    for phrase, points in RULES.items():

        if phrase in text:

            score += points

            matches.append(
                f"{phrase} (+{points})"
            )


    # Detect URLs

    urls = re.findall(
        r"(https?://[^\s]+|www\.[^\s]+|\b[a-zA-Z0-9-]+\.(com|net|org|xyz|io|co)\b)",
        text
    )

    if urls:

        score += 2

        matches.append(
            "external website (+2)"
        )


    return score, matches


# =========================
# BOT READY
# =========================

@bot.event
async def on_ready():

    print(
        f"Bot connected as {bot.user}"
    )

    print(
        "Crypto Scam Detector is online."
    )


# =========================
# IMAGE SCANNER
# =========================

@bot.event
async def on_message(message):
    print(f"📩 MESSAGE RECEIVED: {message.author} | attachments: {len(message.attachments)}")

    if message.author.bot:
        return


    # Only inspect messages containing attachments

    if message.attachments:

        for attachment in message.attachments:

            content_type = (
                attachment.content_type or ""
            )


            # Only images

            if not content_type.startswith(
                "image/"
            ):

                continue


            try:

                print(
                    f"Scanning image from {message.author}..."
                )


                image_bytes = (
                    await attachment.read()
                )


                # OCR

                text = extract_text(
                    image_bytes
                )


                # Scam score

                score, matches = (
                    detect_scam(text)
                )


                print(
                    "=============================="
                )

                print(
                    f"USER: {message.author}"
                )

                print(
                    f"SCORE: {score}"
                )

                print(
                    f"MATCHES: {matches}"
                )

                print(
                    f"OCR TEXT: {text[:1000]}"
                )

                print(
                    "=============================="
                )


                if matches:

    print(
        "🚨 POSSIBLE CRYPTO SCAM DETECTED"
    )

    user_id = message.author.id

    try:
        await message.delete()
        print("🗑️ Message deleted.")

    except Exception as error:
        print(f"DELETE ERROR: {error}")

    if user_id in flagged_users:

        try:
            await message.author.ban(
                reason="Repeated crypto scam image"
            )

            print(
                f"🔨 BANNED: {message.author}"
            )

        except Exception as error:
            print(f"BAN ERROR: {error}")

    else:

        flagged_users.add(user_id)

        try:
            await message.author.timeout(
                timedelta(minutes=TIMEOUT_MINUTES),
                reason="Crypto scam image"
            )

            print(
                f"⏳ TIMEOUT: {message.author}"
            )

        except Exception as error:
            print(f"TIMEOUT ERROR: {error}"
             )
            


            except Exception as error:

                print(
                    f"OCR ERROR: {error}"
                )
                


    await bot.process_commands(
        message
    )


# =========================
# START
# =========================

if not TOKEN:

    raise RuntimeError(
        "DISCORD_TOKEN environment variable is missing."
    )


# Start web server

web_thread = threading.Thread(
    target=run_web_server,
    daemon=True
)

web_thread.start()


# Start Discord bot

bot.run(TOKEN)
