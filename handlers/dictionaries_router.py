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
from utils.paginator import Paginator

dictionaries_router = Router()
dictionaries_router.message.filter(ChatTypeFilter(chat_types=["private"]))

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

    on_test = State()
    answered = State()

    editing_word = State()
    requesting_new_word = State()

    deleting_word = State()
    searching_word = State()
    dict_is_open = State()


def get_btns_menu_dict(dict_name):
    return {
        "⬅️": "swipe_left",
        "➡️": "swipe_right",
        "🔢 Select Page": f"go_to_page.{dict_name}",
        "🔎 Search Words": f"search_words.{dict_name}",
        "➕ Add Words": f"add_words.{dict_name}",
        "🗑️ Delete Words": f"delete_words.{dict_name}",
        "✏️ Edit Words": f"edit_words.{dict_name}",
        "🔙 Back": "back_to_dictionaries"
    }


@dictionaries_router.callback_query(F.data == "view_dicts")
async def view_dicts(callback: CallbackQuery):
    user_dictionaries = await db.get_user_dictionaries(callback.from_user.id)

    # Display the user's dictionaries with emojis
    dictionaries = list(enumerate(user_dictionaries.keys(), start=1))
    btns = {emoji_nums[num]: f"view_dict_{dict_name}" for num, dict_name in dictionaries}
    btns.update({
        "➕ Add Dictionary": "add_dict",
        "🗑️ Delete Dictionary": "delete_dict",
        "🔙 Back": "back_to_functions"
    })
    dict_list_text = "\n".join(
        f"{emoji_nums[i]} <b>{name}</b>" for i, name in dictionaries) if dictionaries else "No dictionaries yet."
    await callback.message.edit_text(
        f"📚 <b>{callback.from_user.first_name}, your dictionaries:</b>\n\n"
        "=========================\n"
        f"{dict_list_text}",
        reply_markup=get_callback_btns(
            btns=btns,
            sizes=calc_dict_btns(dictionaries)
        ),
        parse_mode="HTML"
    )


@dictionaries_router.callback_query(F.data == "add_dict")
async def add_dict(callback: CallbackQuery, state: FSMContext):
    user_dicts = await db.get_user_dictionaries(callback.from_user.id)
    if len(user_dicts) >= 10:
        await callback.answer("❌ You can't create more than 🔟 dictionaries.", show_alert=True)
        return
    await state.set_state(dict.first_language)
    btns = {f"🌐 {lang}": f"lang_{code}" for lang, code in languages.items()}
    btns.update({
        "❌ Cancel": "back_to_dictionaries"
    })
    await callback.message.edit_text(
        "🌍 <b>Create Dictionary</b>\n\nPlease choose the <b>first language</b>.",
        reply_markup=get_callback_btns(
            btns=btns,
            sizes=(4, 3, 2, 1)
        ),
        parse_mode="HTML"
    )


@dictionaries_router.callback_query(F.data == "delete_dict")
async def delete_dict(callback: CallbackQuery):
    user_dictionaries = await db.get_user_dictionaries(callback.from_user.id)

    # Display the user's dictionaries with emojis
    dictionaries = list(enumerate(user_dictionaries.keys(), start=1))
    btns = {emoji_nums[num]: f"confirm_delete_{dict_name}" for num, dict_name in dictionaries}
    btns.update({
        "🛑 Cancel": "back_to_dictionaries"
    })
    dict_list_text = "\n".join(
        f"{emoji_nums[i]} <b>{name}</b>" for i, name in dictionaries) if dictionaries else "No dictionaries yet."
    await callback.message.edit_text(
        f"🗑️ <b>{callback.from_user.first_name}, choose a dictionary to delete:</b>\n\n"
        "=========================\n"
        f"{dict_list_text}",
        reply_markup=get_callback_btns(
            btns=btns,
            sizes=calc_dict_btns(dictionaries)
        ),
        parse_mode="HTML"
    )


@dictionaries_router.callback_query(F.data.startswith("lang_"), dict.first_language)
async def process_dict_name(callback: CallbackQuery, state: FSMContext):
    first_lang_code = callback.data.split("_")[1]
    await state.update_data(first_language=first_lang_code)
    await state.set_state(dict.second_language)
    btns = {f"🌐 {lang}": f"lang_{code}" for lang, code in languages.items() if code != first_lang_code}
    btns.update({
        "❌ Cancel": "back_to_dictionaries"
    })
    await callback.message.edit_text(
        f"🌍 <b>Choose the second language</b>\n\nFirst language selected: <b>{first_lang_code}</b>\n\nPlease choose the second language.",
        reply_markup=get_callback_btns(
            btns=btns,
            sizes=(4, 3, 2, 1)
        ),
        parse_mode="HTML"
    )


@dictionaries_router.callback_query(F.data.startswith("confirm_delete_"))
async def confirm_deleting(callback: CallbackQuery):
    dict_name = callback.data.split("_")[2]
    await callback.message.edit_text(
        f"🗑️ <b>Confirm Deletion</b>\n\nAre you sure you want to delete the dictionary <b>{dict_name}</b>?",
        reply_markup=get_callback_btns(
            btns={
                "✅ Confirm": f"delete_dict_{dict_name}",
                "🔙 Back": "back_to_dictionaries"
            },
            sizes=(1, 1)
        ),
        parse_mode="HTML"
    )


@dictionaries_router.callback_query(F.data.startswith("delete_dict_"))
async def confirm_delete_dict(callback: CallbackQuery):
    dict_name = callback.data.split("_")[2]
    await db.delete_dictionary(callback.from_user.id, dict_name)
    await callback.answer(f"🗑️ Dictionary <b>{dict_name}</b> deleted successfully!", show_alert=True)
    user_dictionaries = await db.get_user_dictionaries(callback.from_user.id)

    # Display the user's dictionaries with emojis
    dictionaries = list(enumerate(user_dictionaries.keys(), start=1))
    btns = {emoji_nums[num]: f"view_dict_{dict_name}" for num, dict_name in dictionaries}
    btns.update({
        "➕ Add Dictionary": "add_dict",
        "🗑️ Delete Dictionary": "delete_dict",
        "🔙 Back": "back_to_functions"
    })
    dict_list_text = "\n".join(
        f"{emoji_nums[i]} <b>{name}</b>" for i, name in dictionaries) if dictionaries else "No dictionaries yet."
    await callback.message.edit_text(
        f"📚 <b>{callback.from_user.first_name}, your dictionaries:</b>\n\n"
        "=========================\n"
        f"{dict_list_text}",
        reply_markup=get_callback_btns(
            btns=btns,
            sizes=calc_dict_btns(dictionaries)
        ),
        parse_mode="HTML"
    )


@dictionaries_router.callback_query(F.data == "back_to_dictionaries")
async def back_to_dictionaries(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    user_dictionaries = await db.get_user_dictionaries(callback.from_user.id)

    # Display the user's dictionaries with emojis
    dictionaries = list(enumerate(user_dictionaries.keys(), start=1))
    btns = {emoji_nums[num]: f"view_dict_{dict_name}" for num, dict_name in dictionaries}
    btns.update({
        "➕ Add Dictionary": "add_dict",
        "🗑️ Delete Dictionary": "delete_dict",
        "🔙 Back": "back_to_functions"
    })
    dict_list_text = "\n".join(
        f"{emoji_nums[i]} <b>{name}</b>" for i, name in dictionaries) if dictionaries else "No dictionaries yet."
    await callback.message.edit_text(
        f"📚 <b>{callback.from_user.first_name}, your dictionaries:</b>\n\n"
        "=========================\n"
        f"{dict_list_text}",
        reply_markup=get_callback_btns(
            btns=btns,
            sizes=calc_dict_btns(dictionaries)
        ),
        parse_mode="HTML"
    )


@dictionaries_router.callback_query(F.data.startswith("lang_"), dict.second_language)
async def process_second_lang_name(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    first_language = data.get("first_language")
    second_language = callback.data.split("_")[1]
    dict_name = f"{first_language} ➡️ {second_language}"
    await db.add_user_dictionaries(callback.from_user.id, dict_name)
    await state.clear()
    user_dictionaries = await db.get_user_dictionaries(callback.from_user.id)

    # Display the user's dictionaries
    dictionaries = list(enumerate(user_dictionaries.keys(), start=1))
    btns = {emoji_nums[num]: f"view_dict_{dict_name}" for num, dict_name in dictionaries}
    btns.update({
        "➕ Add Dictionary": "add_dict",
        "🗑️ Delete Dictionary": "delete_dict",
        "🔙 Back": "back_to_functions"
    })
    await callback.answer(f"✅ Dictionary <b>{dict_name}</b> added successfully!", show_alert=True)
    await callback.message.edit_text(
        f"📚 <b>{callback.from_user.first_name}, your dictionaries:</b>\n\n"
        + "=========================\n"
        + "\n".join(f"{emoji_nums[i]} {name}" for i, name in dictionaries),
        reply_markup=get_callback_btns(
            btns=btns,
            sizes=calc_dict_btns(dictionaries)
        ),
        parse_mode="HTML"
    )


@dictionaries_router.callback_query(F.data.startswith("view_dict_"))
async def open_dict(callback: CallbackQuery, state: FSMContext):
    await state.set_state(dict.dict_is_open)
    dict_name = callback.data.split("_")[2]
    await state.update_data(dict_name=dict_name)
    dictionaries = await db.get_user_dictionaries(callback.from_user.id)
    current_dict = list(enumerate(dictionaries.get(dict_name, {}).items()))
    await state.update_data(page=1)
    pg = Paginator(current_dict, 1, 25)
    btns = get_btns_menu_dict(dict_name)

    if current_dict:
        dict_text = (
                f"📖 <b>{dict_name}</b>\n"
                "=========================\n" +
                f"Current page: {pg.page}\n" +
                "\n".join(f"{i + 1}) <b>{pair[0]}</b> - <b>{pair[1]}</b>" for i, pair in pg.get_page())
        )
    else:
        dict_text = f"📖 <b>{dict_name}</b>\n\nNo words in this dictionary yet."

    await callback.message.edit_text(
        dict_text,
        reply_markup=get_callback_btns(
            btns=btns,
            sizes=(2, 3, 2, 1, 1)
        ),
        parse_mode="HTML"
    )


@dictionaries_router.callback_query(F.data == "swipe_left", dict.dict_is_open)
async def swipe_left(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    dict_name = data.get("dict_name")
    page = data.get("page", 1)
    dictionaries = await db.get_user_dictionaries(callback.from_user.id)
    current_dict = list(enumerate(dictionaries.get(dict_name, {}).items()))
    pg = Paginator(current_dict, page, 25)

    if pg.has_previous():
        page_items = pg.get_previous()
        await state.update_data(page=pg.page)
        btns = get_btns_menu_dict(dict_name)
        dict_text = (
                f"📖 <b>{dict_name}</b>\n"
                "=========================\n" +
                f"Current page: {pg.page}\n" +
                "\n".join(f"{i + 1}) <b>{pair[0]}</b> - <b>{pair[1]}</b>" for i, pair in page_items)
        )
        await callback.message.edit_text(
            dict_text,
            reply_markup=get_callback_btns(
                btns=btns,
                sizes=(2, 3, 2, 1, 1)
            ),
            parse_mode="HTML"
        )
    else:
        await callback.answer("❌ This is the first page.", show_alert=True)


@dictionaries_router.callback_query(F.data == "swipe_right", dict.dict_is_open)
async def swipe_right(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    dict_name = data.get("dict_name")
    page = data.get("page", 1)
    dictionaries = await db.get_user_dictionaries(callback.from_user.id)
    current_dict = list(enumerate(dictionaries.get(dict_name, {}).items()))
    pg = Paginator(current_dict, page, 25)

    if pg.has_next():
        page_items = pg.get_next()
        await state.update_data(page=pg.page)
        btns = get_btns_menu_dict(dict_name)
        dict_text = (
                f"📖 <b>{dict_name}</b>\n"
                "=========================\n" +
                f"Current page: {pg.page}\n" +
                "\n".join(f"{i + 1}) <b>{pair[0]}</b> - <b>{pair[1]}</b>" for i, pair in page_items)
        )
        await callback.message.edit_text(
            dict_text,
            reply_markup=get_callback_btns(
                btns=btns,
                sizes=(2, 3, 2, 1, 1)
            ),
            parse_mode="HTML"
        )
    else:
        await callback.answer("❌ This is the last page.", show_alert=True)


@dictionaries_router.callback_query(F.data.startswith("edit_words."))
async def edit_words(callback: CallbackQuery, state: FSMContext):
    await state.set_state(dict.editing_word)
    data = await state.get_data()
    dict_name = data.get("dict_name")
    await callback.message.edit_text(
        "✏️ <b>Edit Words</b>\n\nPlease enter the word you want to edit.",
        reply_markup=get_callback_btns(
            btns={"🔙 Back": f"view_dict_{dict_name}"}
        ),
        parse_mode="HTML"
    )


@dictionaries_router.message(dict.editing_word)
async def request_word_for_edit(message: types.Message, state: FSMContext):
    word = message.text.strip()
    word = word.lower()
    data = await state.get_data()
    dict_name = data.get("dict_name")
    dictionaries = await db.get_user_dictionaries(message.from_user.id)
    current_dict = dictionaries.get(dict_name, {})
    if word in current_dict or word in current_dict.values():
        await state.update_data(word=word)
        await message.answer("✏️ Please enter the new translation:",
                             reply_markup=get_callback_btns(
                                 btns={"🔙 Back": f"view_dict_{dict_name}"}
                             ), parse_mode="HTML"
                             )
        await state.set_state(dict.requesting_new_word)
    else:
        await message.answer("❌ There is no such word in this dictionary.",
                             reply_markup=get_callback_btns(
                                 btns={"🔙 Back": f"view_dict_{dict_name}"}
                             ), parse_mode="HTML"
                             )
        return


@dictionaries_router.message(dict.requesting_new_word)
async def request_new_word_for_edit(message: types.Message, state: FSMContext):
    new_translation = message.text.strip()
    new_translation = new_translation.lower()
    data = await state.get_data()
    dict_name = data.get("dict_name")
    word = data.get("word")
    dictionaries = await db.get_user_dictionaries(message.from_user.id)
    current_dict = dictionaries.get(dict_name, {})
    if word in current_dict or word in current_dict.values():
        await db.edit_word_in_dict(message.from_user.id, dict_name, word, new_translation)
        await message.answer("✅ Word updated successfully!")
    else:
        await message.answer("❌ There was an error updating the word.")
    await state.set_state(dict.dict_is_open)
    dictionaries = await db.get_user_dictionaries(message.from_user.id)
    current_dict = list(enumerate(dictionaries[dict_name].items()))
    btns = get_btns_menu_dict(dict_name)

    await message.answer(
        f"{dict_name}\n=========================\n" +
        "\n".join(f"{i + 1}) {pair[0]} - {pair[1]}" for i, pair in current_dict),
        reply_markup=get_callback_btns(
            btns=btns,
            sizes=(2, 3, 2, 1, 1)
        )
    )


@dictionaries_router.callback_query(F.data.startswith("search_words"))
async def search_words(callback: CallbackQuery, state: FSMContext):
    await state.set_state(dict.searching_word)
    data = await state.get_data()
    dict_name = data.get("dict_name")
    await callback.message.edit_text(
        "🔎 <b>Search Words</b>\n\nPlease enter any word from the pair you want to search.",
        reply_markup=get_callback_btns(
            btns={"🔙 Back": f"view_dict_{dict_name}"}
        ),
        parse_mode="HTML"
    )


@dictionaries_router.message(dict.searching_word)
async def request_search(message: types.Message, state: FSMContext):
    word = message.text.strip()
    word = word.lower()
    data = await state.get_data()
    dict_name = data.get("dict_name")
    dictionaries = await db.get_user_dictionaries(message.from_user.id)
    current_dict = dictionaries.get(dict_name, {})
    translation = None

    if word in current_dict:
        translation = current_dict[word]
        await message.answer(f"🔎 Translation of <b>{word}</b>: <b>{translation}</b>", parse_mode="HTML")
    elif word in current_dict.values():
        translation = next((k for k, v in current_dict.items() if v == word), None)
        await message.answer(f"🔎 Translation of <b>{word}</b>: <b>{translation}</b>", parse_mode="HTML")
    else:
        await message.answer("❌ There is no such word in this dictionary.", parse_mode="HTML")

    btns = get_btns_menu_dict(dict_name)
    dict_items = list(enumerate(current_dict.items()))
    if dict_items:
        dict_text = (
                f"📖 <b>{dict_name}</b>\n"
                "=========================\n" +
                "\n".join(f"{i + 1}) {pair[0]} - {pair[1]}" for i, pair in dict_items)
        )
    else:
        dict_text = f"📖 <b>{dict_name}</b>\n\nNo words in this dictionary yet."
    await message.answer(
        dict_text,
        reply_markup=get_callback_btns(
            btns=btns,
            sizes=(2, 3, 2, 1)
        ),
        parse_mode="HTML"
    )


@dictionaries_router.callback_query(F.data.startswith("delete_words"))
async def delete_words(callback: CallbackQuery, state: FSMContext):
    await state.set_state(dict.deleting_word)
    data = await state.get_data()
    dict_name = data.get("dict_name")
    await callback.message.edit_text(
        "🗑️ <b>Delete Words</b>\n\nPlease enter any word from the pair you want to delete.",
        reply_markup=get_callback_btns(
            btns={"🔙 Back": f"view_dict_{dict_name}"}
        ),
        parse_mode="HTML"
    )


@dictionaries_router.message(dict.deleting_word)
async def request_word_for_delete(message: types.Message, state: FSMContext):
    word = message.text.strip()
    word = word.lower()
    data = await state.get_data()
    dict_name = data.get("dict_name")
    dictionaries = await db.get_user_dictionaries(message.from_user.id)
    current_dict = dictionaries.get(dict_name, {})
    word_to_delete = None

    # Find the word to delete (either key or value)
    if word in current_dict:
        word_to_delete = word
    elif word in current_dict.values():
        word_to_delete = next((k for k, v in current_dict.items() if v == word), None)

    if not word_to_delete:
        await message.answer("❌ There is no such word in this dictionary.")
    else:
        await db.delete_word_from_dict(message.from_user.id, dict_name, word_to_delete)
        await message.answer(f"🗑️ Word pair with '{word}' deleted successfully!")

    await state.set_state(dict.dict_is_open)
    dictionaries = await db.get_user_dictionaries(message.from_user.id)
    current_dict = list(enumerate(dictionaries.get(dict_name, {}).items()))
    btns = get_btns_menu_dict(dict_name)

    await message.answer(
        f"📖 <b>{dict_name}</b>\n=========================\n" +
        "\n".join(f"{i + 1}) {pair[0]} - {pair[1]}" for i, pair in
                  current_dict) if current_dict else f"📖 <b>{dict_name}</b>\n\nNo words in this dictionary yet.",
        reply_markup=get_callback_btns(
            btns=btns,
            sizes=(2, 3, 2, 1)
        ),
        parse_mode="HTML"
    )


@dictionaries_router.callback_query(F.data.contains("add_words"))
async def add_words(callback: CallbackQuery, state: FSMContext):
    await state.set_state(dict.first_word)
    data = await state.get_data()
    dict_name = data.get("dict_name")
    await callback.message.edit_text(
        "📝 <b>Add Words</b>\n\nPlease enter the <b>first word</b> for your pair.",
        reply_markup=get_callback_btns(
            btns={"🔙 Back": f"view_dict_{dict_name}"}
        ),
        parse_mode="HTML"
    )


@dictionaries_router.message(dict.first_word)
async def request_word1(message: types.Message, state: FSMContext):
    word1 = message.text.strip()
    await state.update_data(word1=word1)
    await state.set_state(dict.second_word)
    data = await state.get_data()
    dict_name = data.get("dict_name")
    await message.answer(
        f"📝 First word saved: <b>{word1}</b>\n\n🔤 Please enter the second word for the pair.",
        reply_markup=get_callback_btns(
            btns={"🔙 Back": f"view_dict_{dict_name}"}
        ),
        parse_mode="HTML"
    )


@dictionaries_router.message(dict.second_word)
async def request_word2(message: types.Message, state: FSMContext):
    data = await state.get_data()
    dict_name = data.get("dict_name")
    word1 = data.get("word1")
    word2 = message.text.strip()
    word1 = word1.lower()
    word2 = word2.lower()

    if not word1 or not word2:
        await message.answer("Both words must be provided.")
        return

    await db.add_word_to_dict(message.from_user.id, dict_name, f"{word1}:{word2}")
    await state.set_state(dict.dict_is_open)
    dictionaries = await db.get_user_dictionaries(message.from_user.id)
    current_dict = list(enumerate(dictionaries[dict_name].items()))
    btns = get_btns_menu_dict(dict_name)
    pg = Paginator(current_dict, 1, 25)

    await message.answer(
        f"{dict_name}\n=========================\n" +
        "\n".join(f"{i + 1}) {pair[0]} - {pair[1]}" for i, pair in pg.get_page()),
        reply_markup=get_callback_btns(
            btns=btns,
            sizes=(2, 3, 2, 1, 1)
        )
    )


@dictionaries_router.callback_query(F.data == "back_to_functions")
async def back_to_functions(callback: CallbackQuery):
    await callback.message.edit_text(
        "Hello! 👋\n\nWelcome back! Here you can create your own language dictionaries and practice memorizing words.",
        reply_markup=get_callback_btns(
            btns={
                "📚 My Dictionaries": "view_dicts",
                "📝 Tests": "view_tests"
            },
            sizes=(2, 1)
        )
    )