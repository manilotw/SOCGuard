import logging
import os
import threading
import time

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
from elastic import index_alert
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
subscribers = set()

keyboard = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
keyboard.add(telebot.types.KeyboardButton(STATUS_BUTTON))


def format_event(event):
    status = event["status"]

    if status == "failed":
        icon, label = "❌", "FAILED"
    else:
        icon, label = "✅", "SUCCESS"

    return (
        f"{icon} {label}\n"
        f"Time: {event['timestamp']}\n"
        f"IP: {event['ip_address'] or 'Unknown'}\n"
        f"User: {event['username'] or 'Unknown'}"
    )


def format_alert(alert):
    def value(key):
        if isinstance(alert, dict):
            return alert[key]
        return getattr(alert, key)

    return (
        f"🚨 {value('severity')} — Brute-force detected\n"
        f"IP: {value('ip_address')}\n"
        f"Failed attempts: {value('attempts')}\n"
        f"Start: {value('start_time')}\n"
        f"End: {value('end_time')}"
    )


def notify_new_alerts(alerts, extra_chat_id=None):
    for alert in alerts:
        saved = save_alerts([alert])

        if saved == 0:
            continue

        try:
            result = index_alert(alert)
            logger.info(
                "New alert indexed in Elasticsearch: %s",
                result.get("_id"),
            )
        except Exception:
            logger.exception("Failed to index alert in Elasticsearch")

        recipients = set(subscribers)

        if extra_chat_id is not None:
            recipients.add(extra_chat_id)

        for chat_id in recipients:
            try:
                bot.send_message(chat_id, format_alert(alert))
                logger.info("New alert notification sent")
            except Exception:
                logger.exception("Failed to send alert notification")


def monitor_logs():
    logger.info("Automatic monitoring starts in 30 seconds")
    time.sleep(30)

    while True:
        try:
            events = parse_log()
            save_events(events)

            alerts = detect_brute_force(events)
            notify_new_alerts(alerts)

        except Exception:
            logger.exception("Automatic monitoring failed")

        time.sleep(60)


@bot.message_handler(commands=["start"])
def start(message):
    subscribers.add(message.chat.id)

    bot.send_message(
        message.chat.id,
        "🛡️ Welcome to SOCGuard!\n"
        "Automatic monitoring is enabled.\n"
        "I will check authentication logs every 60 seconds "
        "and notify you about new brute-force alerts.",
        reply_markup=keyboard,
    )


@bot.message_handler(
    func=lambda message: message.text == STATUS_BUTTON
)
def send_status(message):
    chat_id = message.chat.id
    subscribers.add(chat_id)

    try:
        bot.send_message(chat_id, "🔍 Checking authentication logs...")

        init_db()

        events = parse_log()
        alerts = detect_brute_force(events)

        new_events = save_events(events)
        notify_new_alerts(alerts, chat_id)

        recent_events = get_recent_events(5)
        recent_alerts = get_recent_alerts(10)

        bot.send_message(
            chat_id,
            "📊 SOCGuard Status\n"
            f"Events found in logs: {len(events)}\n"
            f"New events saved: {new_events}",
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
        bot.send_message(chat_id, "❌ Permission denied while reading auth.log.")

    except Exception:
        logger.exception("Failed to check SOCGuard status")
        bot.send_message(chat_id, "❌ Failed to check status. Check server logs.")


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

    monitor_thread = threading.Thread(
        target=monitor_logs,
        daemon=True,
    )
    monitor_thread.start()

    bot.infinity_polling()
