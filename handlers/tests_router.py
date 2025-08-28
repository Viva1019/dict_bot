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
    temp_dictionary = {}
    for i in dictionary.items():
        temp_dictionary.update({i[1]: i[0]})
    return temp_dictionary

@tests_router.callback_query(F.data == "view_tests")
async def view_tests(callback: CallbackQuery, state: FSMContext):
    await state.set_state(dict.on_test)
    user_dictionaries = await db.get_user_dictionaries(callback.from_user.id)
    dictionaries = list(enumerate(user_dictionaries.keys(), start=1))
    btns = {emoji_nums[num]: f"choosetest_{dict_name}" for num, dict_name in dictionaries}
    btns.update({
        "Back": "back_to_functions"
    })

    await callback.message.edit_text(
        f"{callback.from_user.first_name}, choose dictionary to test:\n\n"+
        "\n=========================\n"+
        "\n".join(f"{i}) {pair}" for i, pair in dictionaries),
        reply_markup=get_callback_btns(
            btns=btns,
            sizes=calc_dict_btns(dictionaries)
        )
    )
async def send_question(callback: CallbackQuery, state: FSMContext):
    """
    Отправляет очередной вопрос пользователю.
    Берёт данные из FSMContext (слова и индекс).
    Если дошли до конца — перемешивает и начинает заново.
    """
    data = await state.get_data()
    dict_name = data["selected_dict"]
    words_list = data["words_list"]
    current_index = data["current_index"]

    # если все слова показаны — перемешиваем и начинаем заново
    if current_index >= len(words_list):
        random.shuffle(words_list)
        current_index = 0
        await state.update_data(words_list=words_list, current_index=current_index)

    # текущее слово
    word, right_ans = words_list[current_index]

    # варианты: правильный + 4 случайных других
    all_translations = [t for _, t in words_list if t != right_ans]
    wrong_answers = random.sample(all_translations, min(4, len(all_translations)))
    words_to_answer = [right_ans] + wrong_answers
    random.shuffle(words_to_answer)

    # сохраняем прогресс
    await state.update_data(
        words_to_answer=words_to_answer,
        right_ans=right_ans,
        question_word=word
    )

    # кнопки
    btns = {ans: f"answer_{ans}_{right_ans}" for ans in words_to_answer}
    btns.update({"Back": "back_to_tests"})

    await callback.message.edit_text(
        f"What is the translation of {word}?",
        reply_markup=get_callback_btns(btns=btns, sizes=(3, 2, 1))
    )

@tests_router.callback_query(F.data.startswith("choosetest_"))
async def process_test_selection(callback: CallbackQuery, state: FSMContext):
    dict_name = callback.data.split("_")[1]
    splited_dict_name = dict_name.split(" -> ")
    reversed_dict_name = " -> ".join([splited_dict_name[1], splited_dict_name[0]])
    btns = {
        dict_name: f"choose_test_{dict_name}",
        reversed_dict_name: f"choose_test_reversed_{dict_name}",
        "Back": "back_to_tests"
    }
    await callback.message.edit_text(
        "Choose test option:",
        reply_markup=get_callback_btns(
            btns=btns,
            sizes=(1, 1, 1)
        )
    )
# старт теста
@tests_router.callback_query(F.data.startswith("choose_test_"))
async def process_test_selection(callback: CallbackQuery, state: FSMContext):
    if "reversed" in callback.data:
        dict_name = callback.data.split("_")[3]
        words_from_dicts = await db.get_user_dictionaries(callback.from_user.id)
        words_from_dict = reverse_dict(words_from_dicts[dict_name])
    else:
        dict_name = callback.data.split("_")[2]
        words_from_dicts = await db.get_user_dictionaries(callback.from_user.id)
        words_from_dict = words_from_dicts[dict_name]

    if len(words_from_dict) < 5:
        await callback.answer(
            f"Dictionary '{dict_name}' has less than 5 words. Please add more words to start a test.",
            show_alert=True
        )
        return

    words_list = list(words_from_dict.items())
    random.shuffle(words_list)

    await state.set_state(dict.on_test)
    await state.update_data(
        selected_dict=dict_name,
        words_list=words_list,
        current_index=0
    )

    await send_question(callback, state)


# обработка ответа
@tests_router.callback_query(F.data.startswith("answer_"), StateFilter(dict.on_test))
async def process_answer(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    current_ans = callback.data.split("_")[1]
    right_ans = data["right_ans"]
    words_to_answer = data["words_to_answer"]

    # отметки
    marked_answers = []
    for word in words_to_answer:
        if word == right_ans:
            marked_answers.append(f"✅ {word}")
        elif word == current_ans:
            marked_answers.append(f"❌ {word}")
        else:
            marked_answers.append(word)

    btns = {word: f"answer_{word}_{right_ans}" for word in marked_answers}
    btns.update({"Next question": "next_question", "Back": "back_to_tests"})

    prefix = "✅ Correct!\n" if current_ans == right_ans else "❌ Incorrect!\n"
    await callback.message.edit_text(
        prefix + callback.message.text,
        reply_markup=get_callback_btns(btns=btns, sizes=(3, 2, 1, 1))
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
async def procces_answer_after_answered(callback: CallbackQuery):
    await callback.answer()

@tests_router.callback_query(F.data == "back_to_tests", or_f(StateFilter(dict.on_test), StateFilter(dict.answered)))
async def back_to_tests(callback: CallbackQuery, state: FSMContext):
    user_dictionaries = await db.get_user_dictionaries(callback.from_user.id)
    dictionaries = list(enumerate(user_dictionaries.keys(), start=1))
    btns = {emoji_nums[num]: f"choosetest_{dict_name}" for num, dict_name in dictionaries}
    btns.update({
        "Back": "back_to_functions"
    })

    await callback.message.edit_text(
        f"{callback.from_user.first_name}, choose dictionary to test:\n\n"+
        "\n=========================\n"+
        "\n".join(f"{i}) {pair}" for i, pair in dictionaries),
        reply_markup=get_callback_btns(
            btns=btns,
            sizes=calc_dict_btns(dictionaries)
        )
    )