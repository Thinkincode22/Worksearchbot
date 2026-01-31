"""Обробники фільтрів"""
from telegram import Update
from telegram.ext import ContextTypes
from bot.keyboards.filters_keyboard import (
    get_filters_keyboard,
    get_city_keyboard,
    get_category_keyboard,
    get_employment_type_keyboard
)
from bot.keyboards.main_menu import get_back_to_menu_keyboard
from bot.handlers.search import user_search_state


async def filters_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обробник команди /filters та кнопки фільтрів"""
    query = update.callback_query or update.message
    
    if update.callback_query:
        await update.callback_query.answer()
    
    text = "⚙️ <b>Налаштування фільтрів</b>\n\nОберіть параметр для налаштування:"
    
    if hasattr(query, 'edit_message_text'):
        await query.edit_message_text(
            text,
            reply_markup=get_filters_keyboard(),
            parse_mode="HTML"
        )
    else:
        await query.reply_text(
            text,
            reply_markup=get_filters_keyboard(),
            parse_mode="HTML"
        )


async def filter_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обробник callback для фільтрів"""
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    data = query.data
    
    # Ініціалізуємо стан якщо немає
    if user_id not in user_search_state:
        user_search_state[user_id] = {"filters": {}}
    if "filters" not in user_search_state[user_id]:
        user_search_state[user_id]["filters"] = {}
    
    if data == "filters":
        await filters_handler(update, context)
    
    elif data == "filter_city":
        current_city = user_search_state[user_id]["filters"].get("city")
        await query.edit_message_text(
            "🏙️ Оберіть місто:",
            reply_markup=get_city_keyboard(current_city),
            parse_mode="HTML"
        )
    
    elif data.startswith("city_"):
        city = data.replace("city_", "")
        if city == "all":
            user_search_state[user_id]["filters"].pop("city", None)
        else:
            user_search_state[user_id]["filters"]["city"] = city
        await query.edit_message_text(
            f"✅ Місто встановлено: {city if city != 'all' else 'Всі міста'}",
            reply_markup=get_filters_keyboard(),
            parse_mode="HTML"
        )
    
    elif data == "filter_category":
        current_category = user_search_state[user_id]["filters"].get("category")
        await query.edit_message_text(
            "📋 Оберіть категорію:",
            reply_markup=get_category_keyboard(current_category),
            parse_mode="HTML"
        )
    
    elif data.startswith("category_"):
        category = data.replace("category_", "")
        if category == "all":
            user_search_state[user_id]["filters"].pop("category", None)
        else:
            user_search_state[user_id]["filters"]["category"] = category
        await query.edit_message_text(
            f"✅ Категорія встановлена: {category if category != 'all' else 'Всі категорії'}",
            reply_markup=get_filters_keyboard(),
            parse_mode="HTML"
        )
    
    elif data == "filter_employment":
        current_type = user_search_state[user_id]["filters"].get("employment_type")
        await query.edit_message_text(
            "⏰ Оберіть тип зайнятості:",
            reply_markup=get_employment_type_keyboard(current_type),
            parse_mode="HTML"
        )
    
    elif data.startswith("employment_"):
        emp_type = data.replace("employment_", "")
        if emp_type == "all":
            user_search_state[user_id]["filters"].pop("employment_type", None)
        else:
            user_search_state[user_id]["filters"]["employment_type"] = emp_type
        await query.edit_message_text(
            f"✅ Тип зайнятості встановлено: {emp_type if emp_type != 'all' else 'Всі типи'}",
            reply_markup=get_filters_keyboard(),
            parse_mode="HTML"
        )
    
    elif data == "filter_salary":
        user_search_state[user_id]["waiting_for"] = "salary"
        await query.edit_message_text(
            "💰 Введіть мінімальну зарплату (PLN):\n\nНаприклад: 5000",
            reply_markup=get_back_to_menu_keyboard(),
            parse_mode="HTML"
        )
    
    elif data == "filter_keywords":
        user_search_state[user_id]["waiting_for"] = "keywords"
        await query.edit_message_text(
            "🔑 Введіть ключові слова через кому:\n\nНаприклад: Python, Developer, Remote",
            reply_markup=get_back_to_menu_keyboard(),
            parse_mode="HTML"
        )
    
    elif data == "filter_reset":
        user_search_state[user_id]["filters"] = {}
        user_search_state[user_id].pop("waiting_for", None)
        await query.edit_message_text(
            "✅ Фільтри скинуто",
            reply_markup=get_filters_keyboard(),
            parse_mode="HTML"
        )
