import os
import random
from typing import Any

from aiogram import F, Router, types
from aiogram.filters import CommandStart
from aiogram.fsm import state
from aiogram.types import KeyboardButton, ReplyKeyboardMarkup, ReplyKeyboardRemove
from aiogram.filters import Command, StateFilter, or_f
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery

from filters.chat_types import ChatTypeFilter

from kbds.inline import get_callback_btns, calc_dict_btns

from db.init_db import db

from handlers.dictionaries_router import dict, emoji_nums

from handlers.dictionaries_router import dictionaries_router
from handlers.tests_router import tests_router

main_router = Router()
main_router.message.filter(ChatTypeFilter(chat_types=["private"]))

main_router.include_router(dictionaries_router)
main_router.include_router(tests_router)

async def check_user(user_id: int) -> bool:
    user_data_local = await db.get_user_data(user_id)
    if not user_data_local:
        await db.add_user(user_id)
    return True

@main_router.message(CommandStart())
async def cmd_start(message: types.Message):
    await check_user(message.from_user.id)

    await message.answer(
        "👋 Hello!\n\n"
        "Welcome to the bot where you can create your own language dictionaries 📚 and practice memorizing words 📝.",
        reply_markup=get_callback_btns(
            btns={
                "📚 My Dictionaries": "view_dicts",
                "📝 Tests": "view_tests"
            },
            sizes=(2, 1)
        )
    )
