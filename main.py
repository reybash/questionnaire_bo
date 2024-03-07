import logging
import asyncio
from message_handlers import router
from aiogram import Dispatcher, Bot
from config import TELEGRAM_TOKEN


async def main():
    dp = Dispatcher()
    bot = Bot(token=TELEGRAM_TOKEN)
    logging.basicConfig(level=logging.INFO)
    dp.include_router(router)
    await dp.start_polling(bot)


if __name__ == '__main__':
    asyncio.run(main())
