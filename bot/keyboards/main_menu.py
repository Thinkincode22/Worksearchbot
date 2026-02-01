"""Головне меню бота"""
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from config.constants import EMOJIS


def get_main_menu_keyboard() -> InlineKeyboardMarkup:
    """Створює клавіатуру головного меню"""

    keyboard = [
        [
            InlineKeyboardButton(
                f"{EMOJIS['search']} Пошук вакансій",
                callback_data="search"
            )
        ]
    ]

    return InlineKeyboardMarkup(keyboard)


def get_back_to_menu_keyboard() -> InlineKeyboardMarkup:
    """Кнопка повернення до головного меню"""
    keyboard = [[
        InlineKeyboardButton(
            f"{EMOJIS['back']} Головне меню",
            callback_data="main_menu"
        )
    ]]
    return InlineKeyboardMarkup(keyboard)
