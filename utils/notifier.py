# quant_project/utils/notifier.py

from telegram import Bot
import config

class Notifier:
    def __init__(self):
        self.bot = Bot(token=config.TELEGRAM_BOT_TOKEN)

    async def send(self, text):
        await self.bot.send_message(chat_id=config.TELEGRAM_CHAT_ID, text=text)
