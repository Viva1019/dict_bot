from aiogram.types import InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

def get_callback_btns(*, btns: dict[str, str], sizes: tuple = (2,)):
    keyboard = InlineKeyboardBuilder()

    for text, data in btns.items():
        keyboard.add(InlineKeyboardButton(text=text, callback_data=data))

    return keyboard.adjust(*sizes).as_markup()

def calc_dict_btns(dictionaries: list[str]) -> tuple[int, int]:
    return len(dictionaries) // 2 + len(dictionaries) % 2, 2
