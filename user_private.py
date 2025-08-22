import os

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

from db.models import Database

user_private_router = Router()
user_private_router.message.filter(ChatTypeFilter(chat_types=["private"]))

db_config = {
    "database": os.getenv("DB_NAME"),
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD"),
    "host": os.getenv("DB_HOST"),
    "port": os.getenv("DB_PORT")
}

emoji_nums = {
    1: "1️⃣",
    2: "2️⃣",
    3: "3️⃣",
    4: "4️⃣",
    5: "5️⃣",
    6: "6️⃣",
    7: "7️⃣",
    8: "8️⃣",
    9: "9️⃣",
    10: "🔟"
}

languages = {
    "🇬🇧 English": "🇬🇧 English",
    "🇪🇸 Spanish": "🇪🇸 Spanish",
    "🇫🇷 French": "🇫🇷 French",
    "🇩🇪 German": "🇩🇪 German",
    "🇮🇹 Italian": "🇮🇹 Italian",
    "🇵🇹 Portuguese": "🇵🇹 Portuguese",  # можно поменять на 🇧🇷 если ориентируешься на Бразилию
    "🇷🇺 Russian": "🇷🇺 Russian",
    "🇨🇳 Chinese": "🇨🇳 Chinese",  # упрощённый китайский (zh-Hans)
    "🇯🇵 Japanese": "🇯🇵 Japanese",
    "🇰🇷 Korean": "🇰🇷 Korean"
}

db = Database(db_config)


class dict(StatesGroup):
    first_language = State()
    second_language = State()


start_message = ""

user_data = ""


async def check_user(user_id: int) -> bool:
    global user_data
    if not user_data:
        await db.connect()
        user_data = await db.get_user_data(user_id)
        if not user_data:
            await db.add_user(user_id)
        await db.close()
    return user_data is not None


@user_private_router.message(CommandStart())
async def cmd_start(message: types.Message):
    global start_message
    try:
        await start_message.delete()
    except:
        pass

    await check_user(message.from_user.id)

    start_message = await message.answer(
        "Hello! \n\n In this bot you can create your own language dictionaries and train in memorizing words.",
        reply_markup=get_callback_btns(
            btns={
                "My Dictionaries": "view_dicts",
                "Tests": "view_tests"
            },
            sizes=(2, 1)
        )
    )


@user_private_router.callback_query(F.data == "view_dicts")
async def view_dicts(callback: CallbackQuery):
    await db.connect()

    user_dictionaries = await db.get_user_dictionaries(callback.from_user.id)

    # Display the user's dictionaries
    dictionaries = list(enumerate(user_dictionaries.keys(), start=1))
    btns = {emoji_nums[num]: f"view_dict_{dict_name}" for num, dict_name in dictionaries}
    btns.update({
        "Add Dictionary": "add_dict",
        "Delete Dictionary": "delete_dict",
        "Back": "back_to_functions"
    })
    await callback.message.edit_text(f"{callback.from_user.first_name}, your dictionaries:\n\n"
                                     + "=========================\n"
                                     + "\n".join(f"{i}. {name}" for i, name in dictionaries),
                                     reply_markup=get_callback_btns(
                                         btns=btns,
                                         sizes=(2, 2, 1)
                                     )
									)
    await db.close()


@user_private_router.callback_query(F.data == "add_dict")
async def add_dict(callback: CallbackQuery, state: FSMContext):
    await state.set_state(dict.first_language)
    btns = {lang: f"lang_{code}" for lang, code in languages.items()}
    btns.update({
        "Cancel": "back_to_dictionaries"
    })
    await callback.message.edit_text("Please choose first language.", reply_markup=get_callback_btns(
        btns=btns,
        sizes=(4, 3, 2, 1)
    ))


@user_private_router.callback_query(F.data.startswith("lang_"), dict.first_language)
async def process_dict_name(callback: CallbackQuery, state: FSMContext):
    await state.update_data(first_language=callback.data.split("_")[1])
    await state.set_state(dict.second_language)
    btns = {lang: f"lang_{code}" for lang, code in languages.items()}
    btns.update({
        "Cancel": "back_to_dictionaries"
    })
    await callback.message.edit_text("Please choose second language.", reply_markup=get_callback_btns(
        btns=btns,
        sizes=(4, 3, 2, 1)
    ))


@user_private_router.callback_query(F.data == "back_to_dictionaries")
async def back_to_dictionaries(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await db.connect()

    user_dictionaries = await db.get_user_dictionaries(callback.from_user.id)

    # Display the user's dictionaries
    dictionaries = list(enumerate(user_dictionaries.keys(), start=1))
    btns = {emoji_nums[num]: f"view_dict_{dict_name}" for num, dict_name in dictionaries}
    btns.update({
        "Add Dictionary": "add_dict",
        "Delete Dictionary": "delete_dict",
        "Back": "back_to_functions"
    })
    await callback.message.edit_text(f"{callback.from_user.first_name}, your dictionaries:\n\n"
                                     + "=========================\n"
                                     + "\n".join(f"{i}. {name}" for i, name in dictionaries),
                                     reply_markup=get_callback_btns(
                                         btns=btns,
                                         sizes=(2, 2, 1)
                                     )
                                     )
    await db.close()

@user_private_router.callback_query(F.data.startswith("lang_"), dict.second_language)
async def process_second_lang_name(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    first_language = data.get("first_language")
    second_language = callback.data.split("_")[1]
    await db.connect()
    await db.add_user_dictionaries(callback.from_user.id, f"{first_language} -> {second_language}")
    await state.clear()
    user_dictionaries = await db.get_user_dictionaries(callback.from_user.id)

    # Display the user's dictionaries
    dictionaries = list(enumerate(user_dictionaries.keys(), start=1))
    btns = {emoji_nums[num]: f"view_dict_{dict_name}" for num, dict_name in dictionaries}
    btns.update({
        "Add Dictionary": "add_dict",
        "Delete Dictionary": "delete_dict",
        "Back": "back_to_functions"
    })
    await callback.message.edit_text(f"{callback.from_user.first_name}, your dictionaries:\n\n"
                                     + "=========================\n"
                                     + "\n".join(f"{i}. {name}" for i, name in dictionaries),
                                     reply_markup=get_callback_btns(
                                         btns=btns,
                                         sizes=(2, 2, 1)
                                     )
                                     )
    await db.close()


@user_private_router.callback_query(F.data == "back_to_functions")
async def back_to_functions(callback: CallbackQuery):
    await callback.message.edit_text(
        "Hello! \n\n In this bot you can create your own language dictionaries and train in memorizing words.",
        reply_markup=get_callback_btns(
            btns={
                "My Dictionaries": "view_dicts",
                "Tests": "view_tests"
            },
            sizes=(2, 1)
        )
    )
