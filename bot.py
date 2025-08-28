import asyncio
import os

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from dotenv import find_dotenv, load_dotenv

from handlers.dictionaries_router import dictionaries_router
from handlers.tests_router import tests_router

from db.init_db import db

load_dotenv(find_dotenv())


bot = Bot(token=os.getenv('TOKEN'),
          default=DefaultBotProperties(parse_mode=ParseMode.HTML))

dp = Dispatcher()

dp.include_router(dictionaries_router)
dp.include_router(tests_router)

async def on_startup():
    await db.connect()
    
async def on_shutdown():
    await db.close()


async def main():

    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)

    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())

asyncio.run(main())
