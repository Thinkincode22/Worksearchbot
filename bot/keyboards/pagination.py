"""Клавіатури для пагінації"""
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from config.constants import EMOJIS


def get_pagination_keyboard(
    page: int,
    total_pages: int,
    job_id: int = None,
    is_favorite: bool = False
) -> InlineKeyboardMarkup:
    """Створює клавіатуру для пагінації"""
    keyboard = []
    
    # Навігація (тільки якщо є більше однієї сторінки)
    if total_pages > 1:
        prev_page = page - 1 if page > 1 else total_pages
        next_page = page + 1 if page < total_pages else 1
        
        nav_row = [
            InlineKeyboardButton(
                "⬅️ Попередня",
                callback_data=f"page_{prev_page}"
            ),
            InlineKeyboardButton(
                f"📄 {page}/{total_pages}",
                callback_data="page_info"
            ),
            InlineKeyboardButton(
                "Наступна ➡️",
                callback_data=f"page_{next_page}"
            )
        ]
        keyboard.append(nav_row)
    
    return InlineKeyboardMarkup(keyboard)

