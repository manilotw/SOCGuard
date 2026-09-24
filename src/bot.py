import os
import logging
import telebot
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)
TOKEN = os.getenv("BOT_TOKEN")
bot = telebot.TeleBot(TOKEN)

@bot.message_handler(func=lambda message: True)
def echo_all(message):
    logger.info("Received message: %s", message.text)
    bot.reply_to(message, message.text)
    logger.info("Sent reply: %s", message.text)

if __name__ == "__main__":
    logger.info("Bot is starting...")
    print("Бот запущен...")
    bot.infinity_polling()