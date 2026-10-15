
import logging
import os

import telebot
from dotenv import load_dotenv

from database import (
    get_recent_alerts,
    get_recent_events,
    init_db,
    save_alerts,
    save_events,
)
from detector import detect_brute_force
from parser import parse_log


load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)
logger = logging.getLogger(__name__)

TOKEN = os.getenv("BOT_TOKEN")

if not TOKEN:
    raise RuntimeError("BOT_TOKEN is missing from the .env file")

bot = telebot.TeleBot(TOKEN)

STATUS_BUTTON = "📊 Send me status"

keyboard = telebot.types.ReplyKeyboardMarkup(
    resize_keyboard=True,
)
keyboard.add(telebot.types.KeyboardButton(STATUS_BUTTON))


def format_event(event):
    status = event["status"]

    if status == "failed":
        icon = "❌"
        label = "FAILED"
    else:
        icon = "✅"
        label = "SUCCESS"

    return (
        f"{icon} {label}\n"
        f"Time: {event['timestamp']}\n"
        f"IP: {event['ip_address'] or 'Unknown'}\n"
        f"User: {event['username'] or 'Unknown'}"
    )


def format_alert(alert):
    return (
        f"🚨 {alert['severity']} — Brute-force detected\n"
        f"IP: {alert['ip_address']}\n"
        f"Failed attempts: {alert['attempts']}\n"
        f"Start: {alert['start_time']}\n"
        f"End: {alert['end_time']}"
    )


@bot.message_handler(commands=["start"])
def start(message):
    bot.send_message(
        message.chat.id,
        "Welcome to SOCGuard!\n"
        "Press the button to check authentication logs.",
        reply_markup=keyboard,
    )


@bot.message_handler(
    func=lambda message: message.text == STATUS_BUTTON
)
def send_status(message):
    chat_id = message.chat.id

    try:
        bot.send_message(chat_id, "🔍 Checking authentication logs...")

        init_db()

        events = parse_log()
        alerts = detect_brute_force(events)

        new_events = save_events(events)
        new_alerts = save_alerts(alerts)

        recent_events = get_recent_events(5)
        recent_alerts = get_recent_alerts(10)

        bot.send_message(
            chat_id,
            "📊 SOCGuard Status\n"
            f"Events found in logs: {len(events)}\n"
            f"New events saved: {new_events}\n"
            f"New alerts saved: {new_alerts}",
            reply_markup=keyboard,
        )

        bot.send_message(chat_id, "🧾 Latest 5 authentication events:")

        if recent_events:
            for event in recent_events:
                bot.send_message(chat_id, format_event(event))
        else:
            bot.send_message(chat_id, "No authentication events found.")

        bot.send_message(chat_id, "🛡️ Brute-force alerts:")

        if recent_alerts:
            for alert in recent_alerts:
                bot.send_message(chat_id, format_alert(alert))
        else:
            bot.send_message(chat_id, "No brute-force alerts recorded.")

    except PermissionError:
        logger.exception("Permission denied while reading authentication logs")
        bot.send_message(
            chat_id,
            "❌ Permission denied while reading auth.log. "
            "Check the bot user's log permissions.",
        )

    except Exception:
        logger.exception("Failed to check SOCGuard status")
        bot.send_message(
            chat_id,
            "❌ Failed to check status. Check the server logs.",
        )


@bot.message_handler(func=lambda message: True)
def unknown_message(message):
    bot.send_message(
        message.chat.id,
        "Press 📊 Send me status to check the logs.",
        reply_markup=keyboard,
    )


if __name__ == "__main__":
    init_db()
    logger.info("SOCGuard Telegram bot is starting")
    bot.infinity_polling()
