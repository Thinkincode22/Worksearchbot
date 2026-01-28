"""Обробники улюблених вакансій"""
from telegram import Update
from telegram.ext import ContextTypes
from database.database import get_db
from database.models import User, UserFavorite, JobListing
from bot.keyboards.pagination import get_pagination_keyboard
from bot.keyboards.main_menu import get_back_to_menu_keyboard
from bot.utils.formatters import format_job_listing
from bot.utils.db_helpers import get_db_session
from sqlalchemy.orm import Session


async def favorites_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обробник команди /favorites та кнопки улюблених"""
    query = update.callback_query or update.message
    
    if hasattr(query, 'answer'):
        await query.answer()
    
    user_id = update.effective_user.id
    
    with get_db_session() as db:
        # Отримуємо користувача
        db_user = db.query(User).filter(User.telegram_id == user_id).first()
        
        if not db_user:
            text = "❌ Помилка: користувач не знайдений"
        else:
            # Отримуємо улюблені вакансії
            favorites = db.query(UserFavorite).filter(
                UserFavorite.user_id == db_user.id
            ).order_by(UserFavorite.created_at.desc()).limit(50).all()
            
            if not favorites:
                text = "⭐ У вас поки немає улюблених вакансій.\n\nДодайте вакансії в улюблені під час пошуку."
            else:
                job_ids = [f.job_listing_id for f in favorites]
                text = f"⭐ <b>Улюблені вакансії</b>\n\nЗнайдено: {len(favorites)} вакансій"
                
                # Зберігаємо для пагінації
                if not hasattr(context, 'user_data'):
                    context.user_data = {}
                context.user_data[f"favorites_{user_id}"] = job_ids
                context.user_data[f"favorites_page_{user_id}"] = 1
                
                # Показуємо першу вакансію
                if job_ids:
                    await show_favorite_job(update, context, user_id, job_ids[0], 1, len(job_ids))
                    return
    
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


async def show_favorite_job(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    user_id: int,
    job_id: int,
    page: int,
    total_pages: int
):
    """Показує улюблену вакансію"""
    with get_db_session() as db:
        job = db.query(JobListing).filter(JobListing.id == job_id).first()
        
        if not job:
            await update.callback_query.answer("Вакансія не знайдена")
            return
        
        text = format_job_listing(job)
        
        await update.callback_query.edit_message_text(
            text,
            reply_markup=get_pagination_keyboard(page, total_pages, job.id, is_favorite=True),
            parse_mode="HTML",
            disable_web_page_preview=False
        )


async def favorite_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обробник callback для додавання/видалення з улюблених"""
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    data = query.data
    
    with get_db_session() as db:
        db_user = db.query(User).filter(User.telegram_id == user_id).first()
        
        if not db_user:
            await query.answer("Помилка: користувач не знайдений")
            return
        
        if data.startswith("favorite_add_"):
            job_id = int(data.replace("favorite_add_", ""))
            
            # Перевіряємо чи вже в улюблених
            existing = db.query(UserFavorite).filter(
                UserFavorite.user_id == db_user.id,
                UserFavorite.job_listing_id == job_id
            ).first()
            
            if existing:
                await query.answer("Вже в улюблених")
            else:
                favorite = UserFavorite(
                    user_id=db_user.id,
                    job_listing_id=job_id
                )
                db.add(favorite)
                db.commit()
                await query.answer("✅ Додано в улюблені")
        
        elif data.startswith("favorite_remove_"):
            job_id = int(data.replace("favorite_remove_", ""))
            
            favorite = db.query(UserFavorite).filter(
                UserFavorite.user_id == db_user.id,
                UserFavorite.job_listing_id == job_id
            ).first()
            
            if favorite:
                db.delete(favorite)
                db.commit()
                await query.answer("➖ Видалено з улюблених")
                
                # Оновлюємо повідомлення
                job = db.query(JobListing).filter(JobListing.id == job_id).first()
                if job:
                    text = format_job_listing(job)
                    # Отримуємо поточну сторінку з контексту
                    page = context.user_data.get(f"favorites_page_{user_id}", 1)
                    favorites_list = context.user_data.get(f"favorites_{user_id}", [])
                    total_pages = len(favorites_list)
                    
                    await query.edit_message_text(
                        text,
                        reply_markup=get_pagination_keyboard(page, total_pages, job.id, is_favorite=False),
                        parse_mode="HTML",
                        disable_web_page_preview=False
                    )
