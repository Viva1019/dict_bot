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

tests_router = Router()
tests_router.message.filter(ChatTypeFilter(chat_types=["private"]))

def reverse_dict(dictionary):
    """
    Reverses the keys and values of a dictionary.
    Adds an emoji to indicate reversed direction.
    """
    reversed_dict = {v: k for k, v in dictionary.items()}
    return reversed_dict

@tests_router.callback_query(F.data == "view_tests")
async def view_tests(callback: CallbackQuery, state: FSMContext):
    await state.set_state(dict.on_test)
    user_dictionaries = await db.get_user_dictionaries(callback.from_user.id)
    dictionaries = list(enumerate(user_dictionaries.keys(), start=1))
    btns = {f"{emoji_nums[num]}": f"choosetest_{dict_name}" for num, dict_name in dictionaries}
    btns.update({
        "🔙 Back": "back_to_functions"
    })

    dicts_text = "\n".join(f"{emoji_nums[num]} {dict_name}" for num, dict_name in dictionaries)
    await callback.message.edit_text(
        f"📚 <b>{callback.from_user.first_name}</b>, choose a dictionary to test:\n\n"
        f"{dicts_text if dicts_text else 'No dictionaries found.'}",
        reply_markup=get_callback_btns(
            btns=btns,
            sizes=calc_dict_btns(dictionaries)
        ),
        parse_mode="HTML"
    )
    
async def send_question(callback: CallbackQuery, state: FSMContext):
    """
    Sends the next question to the user.
    Uses FSMContext for words and index.
    If all words are shown, reshuffles and starts again.
    """
    data = await state.get_data()
    dict_name = data["selected_dict"]
    words_list = data["words_list"]
    current_index = data["current_index"]

    # If all words shown, reshuffle and restart
    if current_index >= len(words_list):
        random.shuffle(words_list)
        current_index = 0
        await state.update_data(words_list=words_list, current_index=current_index)

    # Current word and correct answer
    word, right_ans = words_list[current_index]

    # Prepare answer options: correct + up to 4 random wrong ones
    all_translations = [t for _, t in words_list if t != right_ans]
    wrong_answers = random.sample(all_translations, min(4, len(all_translations)))
    words_to_answer = [right_ans] + wrong_answers
    random.shuffle(words_to_answer)

    # Emojis for answer options
    btns = {}
    for ans in words_to_answer:
        btns[f"{ans}"] = f"answer_{ans}_{right_ans}"

    btns.update({"🔙 Back": "back_to_tests"})

    # Save progress
    await state.update_data(
        words_to_answer=words_to_answer,
        right_ans=right_ans,
        question_word=word
    )

    await callback.message.edit_text(
        f"❓ <b>What is the translation of:</b> <code>{word}</code>?",
        reply_markup=get_callback_btns(btns=btns, sizes=(3, 2, 1)),
        parse_mode="HTML"
    )

@tests_router.callback_query(F.data.startswith("choosetest_"))
async def process_test_selection(callback: CallbackQuery, state: FSMContext):
    dict_name = callback.data.split("_", 1)[1]
    splited_dict_name = dict_name.split(" -> ")
    if len(splited_dict_name) == 2:
        reversed_dict_name = " -> ".join([splited_dict_name[1], splited_dict_name[0]])
        display_dict_name = f"➡️ {dict_name}"
        display_reversed_name = f"🔄 {reversed_dict_name}"
    else:
        reversed_dict_name = dict_name
        display_dict_name = f"➡️ {dict_name}"
        display_reversed_name = f"🔄 {dict_name}"

    words_from_dicts = await db.get_user_dictionaries(callback.from_user.id)

    if dict_name not in words_from_dicts or len(words_from_dicts[dict_name]) < 5:
        await callback.answer(
            f"❗ Dictionary '{dict_name}' has less than 5 words. Please add more words to start a test.",
            show_alert=True
        )
        return

    btns = {
        display_dict_name: f"choose_test_{dict_name}",
        display_reversed_name: f"choose_test_reversed_{dict_name}",
        "🔙 Back": "back_to_tests"
    }
    await callback.message.edit_text(
        "📝 <b>Choose test option:</b>",
        reply_markup=get_callback_btns(
            btns=btns,
            sizes=(1, 1, 1)
        ),
        parse_mode="HTML"
    )
# старт теста
@tests_router.callback_query(F.data.startswith("choose_test_"))
async def start_test(callback: CallbackQuery, state: FSMContext):
    data_parts = callback.data.split("_")
    is_reversed = "reversed" in callback.data
    dict_name = data_parts[3] if is_reversed else data_parts[2]
    user_dicts = await db.get_user_dictionaries(callback.from_user.id)

    if dict_name not in user_dicts:
        await callback.answer("❗ Dictionary not found.", show_alert=True)
        return

    # Prepare dictionary (reverse if needed)
    words_dict = reverse_dict(user_dicts[dict_name]) if is_reversed else user_dicts[dict_name]
    words_list = list(words_dict.items())
    random.shuffle(words_list)

    # Emoji for test direction
    emoji = "🔄" if is_reversed else "➡️"

    await state.set_state(dict.on_test)
    await state.update_data(
        selected_dict=dict_name,
        words_list=words_list,
        current_index=0,
        is_reversed=is_reversed
    )

    await callback.message.edit_text(
        f"{emoji} <b>Test started!</b>\nDictionary: <b>{dict_name}</b>\n\nLet's begin!",
        parse_mode="HTML"
    )
    await send_question(callback, state)


# обработка ответа
@tests_router.callback_query(F.data.startswith("answer_"), StateFilter(dict.on_test))
async def process_answer(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    current_ans = callback.data.split("_")[1]
    right_ans = data["right_ans"]
    words_to_answer = data["words_to_answer"]

    # Add emoji for correct/incorrect answers
    marked_answers = []
    for word in words_to_answer:
        if word == right_ans:
            marked_answers.append(f"✅ {word}")
        elif word == current_ans:
            marked_answers.append(f"❌ {word}")
        else:
            marked_answers.append(f"▫️ {word}")

    # Disable answer buttons after selection
    btns = {}
    for word in marked_answers:
        btns[word] = "noop"
    btns.update({
        "➡️ Next question": "next_question",
        "🔙 Back": "back_to_tests"
    })

    if current_ans == right_ans:
        prefix = "🎉 <b>Correct!</b>\n"
    else:
        prefix = f"😔 <b>Incorrect!</b>\n<b>Correct answer:</b> {right_ans}\n"

    await callback.message.edit_text(
        prefix + callback.message.text,
        reply_markup=get_callback_btns(btns=btns, sizes=(3, 2, 1, 1)),
        parse_mode="HTML"
    )

    await state.set_state(dict.answered)


# следующий вопрос
@tests_router.callback_query(F.data == "next_question", StateFilter(dict.answered))
async def next_question(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    current_index = data["current_index"] + 1

    await state.update_data(current_index=current_index)
    await state.set_state(dict.on_test)
    await send_question(callback, state)

@tests_router.callback_query(F.data.startswith("answer_"), dict.answered)
async def process_answer_after_answered(callback: CallbackQuery):
    await callback.answer("❗ Please press 'Next question' to continue.", show_alert=True)

@tests_router.callback_query(F.data == "back_to_tests", or_f(StateFilter(dict.on_test), StateFilter(dict.answered)))
async def back_to_tests(callback: CallbackQuery, state: FSMContext):
    user_dictionaries = await db.get_user_dictionaries(callback.from_user.id)
    dictionaries = list(enumerate(user_dictionaries.keys(), start=1))
    btns = {f"{emoji_nums[num]}": f"choosetest_{dict_name}" for num, dict_name in dictionaries}
    btns.update({
        "🔙 Back": "back_to_functions"
    })

    dicts_text = "\n".join(f"{emoji_nums[num]} {dict_name}" for num, dict_name in dictionaries)
    await callback.message.edit_text(
        f"📚 <b>{callback.from_user.first_name}</b>, choose a dictionary to test:\n\n"
        f"{dicts_text if dicts_text else 'No dictionaries found.'}",
        reply_markup=get_callback_btns(
            btns=btns,
            sizes=calc_dict_btns(dictionaries)
        ),
        parse_mode="HTML"
    )