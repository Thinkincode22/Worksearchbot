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
    
    # Навігація
    if total_pages > 1:
        # Основний рядок навігації: [Попередня] [Стор/Разом] [Наступна]
        prev_page = page - 1 if page > 1 else total_pages
        next_page = page + 1 if page < total_pages else 1
        
        row1 = [
            InlineKeyboardButton(f"{EMOJIS['back']} Попередня", callback_data=f"page_{prev_page}"),
            InlineKeyboardButton(f"📄 {page}/{total_pages}", callback_data="page_info"),
            InlineKeyboardButton(f"Наступна {EMOJIS['next']}", callback_data=f"page_{next_page}")
        ]
        keyboard.append(row1)
        
        # Рядок швидкої навігації (якщо сторінок багато)
        if total_pages > 5:
            jump_prev = max(1, page - 5)
            jump_next = min(total_pages, page + 5)
            
            row2 = []
            if page > 1:
                row2.append(InlineKeyboardButton("⏮️ 1", callback_data="page_1"))
            
            if page > 5:
                row2.append(InlineKeyboardButton("-5 ⏪", callback_data=f"page_{jump_prev}"))
            
            if page < total_pages - 5:
                row2.append(InlineKeyboardButton("⏩ +5", callback_data=f"page_{jump_next}"))
                
            if page < total_pages:
                row2.append(InlineKeyboardButton(f"{total_pages} ⏭️", callback_data=f"page_{total_pages}"))
            
            if row2:
                keyboard.append(row2)
    
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
