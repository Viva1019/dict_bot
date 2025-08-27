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

from db.init_db import db


dictionaries_router = Router()
dictionaries_router.message.filter(ChatTypeFilter(chat_types=["private"]))

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


class dict(StatesGroup):
    first_language = State()
    second_language = State()

    first_word = State()
    second_word = State()

    deleting_word = State()
    dict_is_open = State()


async def check_user(user_id: int) -> bool:
    user_data_local = await db.get_user_data(user_id)
    if not user_data_local:
        await db.add_user(user_id)
    return True

@dictionaries_router.message(CommandStart())
async def cmd_start(message: types.Message):
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

@dictionaries_router.callback_query(F.data == "view_dicts")
async def view_dicts(callback: CallbackQuery):
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
                                         sizes=calc_dict_btns(dictionaries)
                                     )
                                     )

@dictionaries_router.callback_query(F.data == "add_dict")
async def add_dict(callback: CallbackQuery, state: FSMContext):
    if len(await db.get_user_dictionaries(callback.from_user.id)) == 10:
        await callback.answer("You can't create more than 10 dictionaries")
        return
    await state.set_state(dict.first_language)
    btns = {lang: f"lang_{code}" for lang, code in languages.items()}
    btns.update({
        "Cancel": "back_to_dictionaries"
    })
    await callback.message.edit_text("Please choose first language.", reply_markup=get_callback_btns(
        btns=btns,
        sizes=(4, 3, 2, 1)
    ))

@dictionaries_router.callback_query(F.data == "delete_dict")
async def delete_dict(callback: CallbackQuery):
    user_dictionaries = await db.get_user_dictionaries(callback.from_user.id)

    # Display the user's dictionaries
    dictionaries = list(enumerate(user_dictionaries.keys(), start=1))
    btns = {emoji_nums[num]: f"confirm_delete_{dict_name}" for num, dict_name in dictionaries}
    btns.update({
        "Cancel": "back_to_dictionaries"
    })
    await callback.message.edit_text(f"{callback.from_user.first_name}, choose dictionary to delete:\n\n"
                                     + "=========================\n"
                                     + "\n".join(f"{i}. {name}" for i, name in dictionaries),
                                     reply_markup=get_callback_btns(
                                         btns=btns,
                                         sizes=calc_dict_btns(dictionaries)
                                     ))

@dictionaries_router.callback_query(F.data.startswith("lang_"), dict.first_language)
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

@dictionaries_router.callback_query(F.data.startswith("confirm_delete_"))
async def confirm_deleting(callback: CallbackQuery):
    dict_name = callback.data.split("_")[2]
    await callback.message.edit_text(f"Confirm deleting dict {dict_name}", reply_markup=(
        get_callback_btns(
            btns={
                "Confirm": f"delete_dict_{dict_name}",
                "Back": "back_to_dictionaries"
            },
            sizes=(1, 1)
        )
    ))

@dictionaries_router.callback_query(F.data.startswith("delete_dict_"))
async def confirm_delete_dict(callback: CallbackQuery):
    dict_name = callback.data.split("_")[1]
    await db.delete_dictionary(callback.from_user.id, dict_name)
    await callback.answer(f"✅ Dictionary '{dict_name}' deleted.")
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
                                         sizes=calc_dict_btns(dictionaries)
                                     )
                                     )

@dictionaries_router.callback_query(F.data == "back_to_dictionaries")
async def back_to_dictionaries(callback: CallbackQuery, state: FSMContext):
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
                                         sizes=calc_dict_btns(dictionaries)
                                     )
                                 )

@dictionaries_router.callback_query(F.data.startswith("lang_"), dict.second_language)
async def process_second_lang_name(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    first_language = data.get("first_language")
    second_language = callback.data.split("_")[1]
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
    await callback.answer(f"✅ Dictionary {first_language} -> {second_language} added successfully")
    await callback.message.edit_text(f"{callback.from_user.first_name}, your dictionaries:\n\n"
                                     + "=========================\n"
                                     + "\n".join(f"{i}. {name}" for i, name in dictionaries),
                                     reply_markup=get_callback_btns(
                                         btns=btns,
                                         sizes=calc_dict_btns(dictionaries)
                                     )
                                     )

@dictionaries_router.callback_query(F.data.startswith("view_dict_"))
async def open_dict(callback: CallbackQuery, state: FSMContext):
    await state.set_state(dict.dict_is_open)
    dict_name = callback.data.split("_")[2]
    await state.update_data(dict_name=dict_name)
    dictionaries = await db.get_user_dictionaries(callback.from_user.id)
    current_dict = enumerate(dictionaries[dict_name].items())
    await state.update_data(current_dict=current_dict)
    btns={
        "<" : "swipe_left",
        ">" : "swipe_right",
        "Add words" : f"add_words.{dict_name}",
        "Delete words" : f"delete_words.{dict_name}",
        "Edit words" : "edit_words",
        "Back" : "back_to_dictionaries"
    }

    await callback.message.edit_text(
        f"{dict_name}"+
        "\n=========================\n"+
        "\n".join(f"{i+1}){pair[0]} - {pair[1]}" for i, pair in current_dict),
        reply_markup=get_callback_btns(
            btns=btns,
            sizes=(2,1,1,1,1)
        )
    )

@dictionaries_router.callback_query(F.data.startswith("delete_words"))
async def delete_words(callback: CallbackQuery, state: FSMContext):
    await state.set_state(dict.deleting_word)
    await state.update_data(dict_name=callback.data.split('.')[1])
    data = await state.get_data()
    dict_name = data.get("dict_name")
    await callback.message.edit_text("Enter any word from the pair",
                                    reply_markup=get_callback_btns(
                                        btns={"Back" : f"view_dict_{dict_name}"}
                                    )
                                  )

@dictionaries_router.message(dict.deleting_word)
async def request_word_for_delete(message: types.Message, state: FSMContext):
    await state.update_data(word = message.text)
    data = await state.get_data()
    word = data.get("word")
    dict_name = data.get("dict_name")
    dictionaries = await db.get_user_dictionaries(message.from_user.id)
    current_dict = dictionaries[dict_name]
    word_to_delete=''
    if word in current_dict:
        word_to_delete = word
    elif word in current_dict.values():
        for key in current_dict:
            if current_dict[key] == word:
                word_to_delete = key
    else:
        await message.answer("there is no such word in this dictionary")
    await db.delete_word_from_dict(message.from_user.id, dict_name, word_to_delete)
    await state.clear()
    dictionaries = await db.get_user_dictionaries(message.from_user.id)
    current_dict = enumerate(dictionaries[dict_name].items())
    btns={
        "<" : "swipe_left",
        ">" : "swipe_right",
        "Add words" : f"add_words.{dict_name}",
        "Delete words" : "delete_words",
        "Edit words" : "edit_words",
        "Back" : "back_to_dictionaries"
    }
    await message.answer(
        f"{dict_name}"+
        "\n=========================\n"+
        "\n".join(f"{i+1}){pair[0]} - {pair[1]}" for i, pair in current_dict),
        reply_markup=get_callback_btns(
            btns=btns,
            sizes=(2,1,1,1,1)
        )
    )

@dictionaries_router.callback_query(F.data.contains("add_words"))
async def add_words(callback: CallbackQuery, state: FSMContext):
    await state.set_state(dict.first_word)
    await state.update_data(dict_name=callback.data.split('.')[1])
    data = await state.get_data()
    dict_name = data.get("dict_name")
    await callback.message.edit_text("Enter first word",
                                    reply_markup=get_callback_btns(
                                        btns={"Back" : f"view_dict_{dict_name}"}
                                    )
                                  )
    
@dictionaries_router.message(dict.first_word)
async def request_word1(message: types.Message, state: FSMContext):
    await state.update_data(word1 = message.text)
    await state.set_state(dict.second_word)
    data = await state.get_data()
    dict_name = data.get("dict_name")
    await message.answer("Enter second word",
                                    reply_markup=get_callback_btns(
                                        btns={"Back" : f"view_dict_{dict_name}"}
                                    )
                                  )

@dictionaries_router.message(dict.second_word)
async def request_word2(message: types.Message, state: FSMContext):
    await state.update_data(word2 = message.text)
    data = await state.get_data()
    dict_name = data.get("dict_name")
    pair = data.get("word1") + ':' + data.get("word2")
    await db.add_word_to_dict(message.from_user.id, dict_name, pair)
    await state.clear()
    dictionaries = await db.get_user_dictionaries(message.from_user.id)
    current_dict = enumerate(dictionaries[dict_name].items())
    btns={
        "<" : "swipe_left",
        ">" : "swipe_right",
        "Add words" : f"add_words.{dict_name}",
        "Delete words" : "delete_words",
        "Edit words" : "edit_words",
        "Back" : "back_to_dictionaries"
    }

    await message.answer(
        f"{dict_name}"+
        "\n=========================\n"+
        "\n".join(f"{i+1}){pair[0]} - {pair[1]}" for i, pair in current_dict),
        reply_markup=get_callback_btns(
            btns=btns,
            sizes=(2,1,1,1,1)
        )
    )

@dictionaries_router.callback_query(F.data == "back_to_functions")
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

