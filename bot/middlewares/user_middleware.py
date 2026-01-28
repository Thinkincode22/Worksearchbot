"""Middleware для автоматичної реєстрації користувачів"""
from telegram import Update
from telegram.ext import ContextTypes, BaseHandler
from database.database import get_db
from database.models import User
from sqlalchemy.orm import Session


class UserMiddleware:
    """Middleware для автоматичної реєстрації користувачів"""
    
    async def __call__(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обробка оновлення"""
        if update.effective_user:
            user = update.effective_user
            db: Session = next(get_db())
            
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
