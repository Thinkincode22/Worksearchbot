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
        ],

        # Нижче — кнопки, які тимчасово приховані.
        # Вони залишаються в коді, бо функціонал у розробці.
        # Коли будемо готові — просто розкоментуємо.

        # [
        #     InlineKeyboardButton(
        #         f"{EMOJIS['filters']} Фільтри",
        #         callback_data="filters"
        #     ),
        #     InlineKeyboardButton(
        #         f"{EMOJIS['favorites']} Улюблені",
        #         callback_data="favorites"
        #     )
        # ],
        # [
        #     InlineKeyboardButton(
        #         f"{EMOJIS['subscriptions']} Підписки",
        #         callback_data="subscriptions"
        #     ),
        #     InlineKeyboardButton(
        #         f"{EMOJIS['stats']} Статистика",
        #         callback_data="stats"
        #     )
        # ]
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
