import asyncio
import os

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from dotenv import find_dotenv, load_dotenv

load_dotenv(find_dotenv())
from handlers.user_private import user_private_router

bot = Bot(token=os.getenv('TOKEN'),
          default=DefaultBotProperties(parse_mode=ParseMode.HTML))

dp = Dispatcher()

dp.include_router(user_private_router)


async def main():
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())


asyncio.run(main())