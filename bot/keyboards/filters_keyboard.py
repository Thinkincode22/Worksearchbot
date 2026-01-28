"""Клавіатури для фільтрів"""
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from config.constants import POLISH_CITIES, JOB_CATEGORIES, EMOJIS, EMPLOYMENT_TYPES


def get_filters_keyboard() -> InlineKeyboardMarkup:
    """Клавіатура налаштування фільтрів"""
    keyboard = [
        [
            InlineKeyboardButton("🏙️ Місто", callback_data="filter_city"),
            InlineKeyboardButton("💰 Зарплата", callback_data="filter_salary")
        ],
        [
            InlineKeyboardButton("📋 Категорія", callback_data="filter_category"),
            InlineKeyboardButton("⏰ Тип роботи", callback_data="filter_employment")
        ],
        [
            InlineKeyboardButton("🔑 Ключові слова", callback_data="filter_keywords"),
            InlineKeyboardButton("❌ Скинути фільтри", callback_data="filter_reset")
        ],
        [
            InlineKeyboardButton(f"{EMOJIS['back']} Назад", callback_data="main_menu")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)


def get_city_keyboard(selected_city: str = None) -> InlineKeyboardMarkup:
    """Клавіатура вибору міста"""
    keyboard = []
    
    # Показуємо перші 12 міст у вигляді кнопок 2x2
    for i in range(0, min(12, len(POLISH_CITIES)), 2):
        row = []
        for j in range(2):
            if i + j < len(POLISH_CITIES):
                city = POLISH_CITIES[i + j]
                prefix = "✅ " if city == selected_city else ""
                row.append(
                    InlineKeyboardButton(
                        f"{prefix}{city}",
                        callback_data=f"city_{city}"
                    )
                )
        keyboard.append(row)
    
    keyboard.append([
        InlineKeyboardButton("Всі міста", callback_data="city_all"),
        InlineKeyboardButton(f"{EMOJIS['back']} Назад", callback_data="filters")
    ])
    
    return InlineKeyboardMarkup(keyboard)


def get_category_keyboard(selected_category: str = None) -> InlineKeyboardMarkup:
    """Клавіатура вибору категорії"""
    keyboard = []
    
    for i in range(0, len(JOB_CATEGORIES), 2):
        row = []
        for j in range(2):
            if i + j < len(JOB_CATEGORIES):
                category = JOB_CATEGORIES[i + j]
                prefix = "✅ " if category == selected_category else ""
                row.append(
                    InlineKeyboardButton(
                        f"{prefix}{category}",
                        callback_data=f"category_{category}"
                    )
                )
        keyboard.append(row)
    
    keyboard.append([
        InlineKeyboardButton("Всі категорії", callback_data="category_all"),
        InlineKeyboardButton(f"{EMOJIS['back']} Назад", callback_data="filters")
    ])
    
    return InlineKeyboardMarkup(keyboard)


def get_employment_type_keyboard(selected_type: str = None) -> InlineKeyboardMarkup:
    """Клавіатура вибору типу зайнятості"""
    keyboard = []
    types_list = list(EMPLOYMENT_TYPES.items())
    
    for i in range(0, len(types_list), 2):
        row = []
        for j in range(2):
            if i + j < len(types_list):
                emp_key, emp_value = types_list[i + j]
                prefix = "✅ " if emp_key == selected_type else ""
                row.append(
                    InlineKeyboardButton(
                        f"{prefix}{emp_value}",
                        callback_data=f"employment_{emp_key}"
                    )
                )
        keyboard.append(row)
    
    keyboard.append([
        InlineKeyboardButton("Всі типи", callback_data="employment_all"),
        InlineKeyboardButton(f"{EMOJIS['back']} Назад", callback_data="filters")
    ])
    
    return InlineKeyboardMarkup(keyboard)
