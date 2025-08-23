from aiogram.types import InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

def get_callback_btns(*, btns: dict[str, str], sizes: tuple = (2,)):
    keyboard = InlineKeyboardBuilder()

    for text, data in btns.items():
        keyboard.add(InlineKeyboardButton(text=text, callback_data=data))

    return keyboard.adjust(*sizes).as_markup()

def calc_dict_btns(dictionaries):
    match len(dictionaries):
        case 0:
            return 2, 1
        case 1:
            return 1, 2, 1
        case 2:
            return 2, 2, 1
        case 3:
            return 3, 2, 1
        case 4:
            return 3, 1, 2, 1
        case 5:
            return 3, 2, 2, 1
        case 6:
            return 4, 2, 2, 1
        case 7:
            return 4, 3, 2, 1
        case 8:
            return 4, 3, 1, 2, 1
        case 9:
            return 4, 3, 2, 2, 1
        case 10:
            return 4, 4, 2, 2, 1
    return None