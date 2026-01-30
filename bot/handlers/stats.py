"""Обробники статистики"""
from telegram import Update
from telegram.ext import ContextTypes
from database.models import JobListing, User
from bot.keyboards.main_menu import get_back_to_menu_keyboard
from bot.utils.formatters import format_stats
from bot.utils.db_helpers import get_db_session
from sqlalchemy.orm import Session
from sqlalchemy import func


async def stats_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обробник команди /stats та кнопки статистики"""
    query = update.callback_query or update.message
    
    if update.callback_query:
        await update.callback_query.answer()
    
    with get_db_session() as db:
        # Збираємо статистику
        total_jobs = db.query(JobListing).filter(JobListing.is_active == True).count()
        total_users = db.query(User).filter(User.is_active == True).count()
        
        # Статистика по містах
        jobs_by_city = db.query(
            JobListing.city,
            func.count(JobListing.id).label('count')
        ).filter(
            JobListing.is_active == True,
            JobListing.city.isnot(None)
        ).group_by(JobListing.city).order_by(func.count(JobListing.id).desc()).limit(10).all()
        
        stats = {
            'total_jobs': total_jobs,
            'total_users': total_users,
            'jobs_by_city': {city: count for city, count in jobs_by_city}
        }
        
        text = format_stats(stats)
    
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
