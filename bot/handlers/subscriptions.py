"""Обробники підписок"""
from telegram import Update
from telegram.ext import ContextTypes
from database.database import get_db
from database.models import User, UserSubscription
from bot.keyboards.main_menu import get_back_to_menu_keyboard
from bot.utils.formatters import format_subscription_info
from bot.utils.db_helpers import get_db_session
from sqlalchemy.orm import Session


async def subscriptions_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обробник команди /subscriptions та кнопки підписок"""
    query = update.callback_query or update.message
    
    if update.callback_query:
        await update.callback_query.answer()
    
    user_id = update.effective_user.id
    
    with get_db_session() as db:
        # Отримуємо користувача
        db_user = db.query(User).filter(User.telegram_id == user_id).first()
        
        if not db_user:
            text = "❌ Помилка: користувач не знайдений"
        else:
            # Отримуємо підписки
            subscriptions = db.query(UserSubscription).filter(
                UserSubscription.user_id == db_user.id
            ).order_by(UserSubscription.created_at.desc()).all()
            
            if not subscriptions:
                text = (
                    "📢 <b>Підписки</b>\n\n"
                    "У вас поки немає активних підписок.\n\n"
                    "Створіть підписку, щоб отримувати сповіщення про нові вакансії за вашими критеріями."
                )
            else:
                text = f"📢 <b>Ваші підписки</b>\n\n"
                for sub in subscriptions[:5]:  # Показуємо перші 5
                    text += format_subscription_info(sub) + "\n\n"
    
    if hasattr(query, 'edit_message_text'):
        await query.edit_message_text(
            text,
            reply_markup=get_back_to_menu_keyboard(),
            parse_mode="HTML"
        )
    else:
        await query.reply_text(
            text,
            reply_markup=get_back_to_menu_keyboard(),
            parse_mode="HTML"
        )


async def subscription_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обробник callback для підписок"""
    query = update.callback_query
    await query.answer()
    
    # Тут можна додати логіку створення/редагування/видалення підписок
    await query.edit_message_text(
        "📢 Функціонал підписок в розробці",
        reply_markup=get_back_to_menu_keyboard(),
        parse_mode="HTML"
    )
