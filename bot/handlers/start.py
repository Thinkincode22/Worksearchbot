"""Обробники команд start та help"""
from telegram import Update
from telegram.ext import ContextTypes
from database.database import get_db
from database.models import User
from bot.keyboards.main_menu import get_main_menu_keyboard
from bot.utils.db_helpers import get_db_session
from config.constants import MESSAGES
from sqlalchemy.orm import Session


async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обробник команди /start"""
    user = update.effective_user
    
    with get_db_session() as db:
        # Перевіряємо чи користувач вже є в БД
        db_user = db.query(User).filter(User.telegram_id == user.id).first()
        
        if not db_user:
            # Створюємо нового користувача
            db_user = User(
                telegram_id=user.id,
                username=user.username,
                first_name=user.first_name,
                language_code=user.language_code or "uk"
            )
            db.add(db_user)
            db.commit()
            db.refresh(db_user)
        
        # Відправляємо привітальне повідомлення
        message = update.message or (update.callback_query.message if update.callback_query else None)
        if message:
            await message.reply_text(
                MESSAGES["start"],
                reply_markup=get_main_menu_keyboard(),
                parse_mode="HTML"
            )
        elif update.callback_query:
            await update.callback_query.edit_message_text(
                MESSAGES["start"],
                reply_markup=get_main_menu_keyboard(),
                parse_mode="HTML"
            )


async def help_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обробник команди /help"""
    await update.message.reply_text(
        MESSAGES["help"],
        parse_mode="HTML"
    )
