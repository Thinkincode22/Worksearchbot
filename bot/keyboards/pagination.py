"""Клавіатури для пагінації"""
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from config.constants import EMOJIS


def get_pagination_keyboard(
    page: int,
    total_pages: int,
    job_id: int = None,
    is_favorite: bool = False
) -> InlineKeyboardMarkup:
    """Створює клавіатуру для пагінації та дій з вакансією"""
    keyboard = []
    
    # Кнопки навігації
    if total_pages > 1:
        # Робимо циклічну пагінацію
        prev_page = page - 1 if page > 1 else total_pages
        next_page = page + 1 if page < total_pages else 1
        
        nav_buttons = [
            InlineKeyboardButton(
                f"{EMOJIS['back']} Попередня",
                callback_data=f"page_{prev_page}"
            ),
            InlineKeyboardButton(
                f"Наступна {EMOJIS['next']}",
                callback_data=f"page_{next_page}"
            )
        ]
        keyboard.append(nav_buttons)
    
    # Кнопки дій з вакансією
    if job_id:
        action_buttons = []
        if is_favorite:
            action_buttons.append(
                InlineKeyboardButton(
                    f"{EMOJIS['remove']} Видалити з улюблених",
                    callback_data=f"favorite_remove_{job_id}"
                )
            )
        else:
            action_buttons.append(
                InlineKeyboardButton(
                    f"{EMOJIS['add']} Додати в улюблені",
                    callback_data=f"favorite_add_{job_id}"
                )
            )
        
        if action_buttons:
            keyboard.append(action_buttons)
    
    # Кнопка повернення
    keyboard.append([
        InlineKeyboardButton(
            f"{EMOJIS['back']} Головне меню",
            callback_data="main_menu"
        )
    ])
    
    return InlineKeyboardMarkup(keyboard)
