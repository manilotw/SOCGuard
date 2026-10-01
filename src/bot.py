import logging
import os
import subprocess
import sys

import telebot
from dotenv import load_dotenv


load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)

logger = logging.getLogger(__name__)

TOKEN = os.getenv("BOT_TOKEN")

if not TOKEN:
    raise RuntimeError("BOT_TOKEN is not set")

bot = telebot.TeleBot(TOKEN)

status_button = telebot.types.ReplyKeyboardMarkup(
    resize_keyboard=True,
)

status_button.add(
    telebot.types.KeyboardButton("📊 Send me status")
)


@bot.message_handler(commands=["start"])
def start(message):
    logger.info("User %s started the bot", message.chat.id)

    bot.send_message(
        message.chat.id,
        "🛡️ SOCGuard\n\n"
        "Press the button below to check authentication status.",
        reply_markup=status_button,
    )


@bot.message_handler(func=lambda message: message.text == "📊 Send me status")
def send_status(message):
    logger.info(
        "Status requested by user %s",
        message.chat.id,
    )

    bot.send_message(
        message.chat.id,
        "🔍 Checking authentication logs...",
    )

    parser_path = os.path.join(
        os.path.dirname(__file__),
        "parser.py",
    )

    try:
        result = subprocess.run(
            [sys.executable, parser_path],
            capture_output=True,
            text=True,
            check=True,
        )

        output = result.stdout

        logger.info("Parser executed successfully")

        events = []

        for line in output.splitlines():
            if not line.startswith("AuthEvent("):
                continue

            events.append(line)

        if not events:
            bot.send_message(
                message.chat.id,
                "📊 No authentication events found.",
            )
            return

        response = "📊 Authentication Status\n\n"

        for event in events:
            if "status='failed'" in event:
                icon = "❌"
                status = "FAILED"
            elif "status='success'" in event:
                icon = "✅"
                status = "SUCCESS"
            else:
                continue

            response += f"{icon} {status}\n"
            response += f"{event}\n\n"

        bot.send_message(
            message.chat.id,
            response,
        )

    except subprocess.CalledProcessError as error:
        logger.exception("Parser failed")

        bot.send_message(
            message.chat.id,
            f"❌ Parser error:\n{error.stderr}",
        )

    except Exception as error:
        logger.exception("Unexpected error")

        bot.send_message(
            message.chat.id,
            f"❌ Error:\n{error}",
        )


if __name__ == "__main__":
    logger.info("Bot is starting...")
    print("Бот запущен...")

    bot.infinity_polling()

