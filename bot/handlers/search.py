"""Обробники пошуку вакансій"""
from telegram import Update
from telegram.ext import ContextTypes
from database.database import get_db
from database.models import JobListing, SearchHistory, User
from bot.keyboards.pagination import get_pagination_keyboard
from bot.keyboards.main_menu import get_back_to_menu_keyboard
from bot.utils.formatters import format_job_listing
from bot.utils.db_helpers import get_db_session
from config.constants import MESSAGES
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_


# Зберігаємо стан пошуку для кожного користувача
user_search_state = {}


async def search_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обробник команди /search та кнопки пошуку"""
    query = update.callback_query or update.message
    
    await query.answer()
    
    text = "🔍 <b>Пошук вакансій</b>\n\nВведіть ключові слова для пошуку або використайте фільтри."
    
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


async def search_query_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обробник текстового запиту для пошуку"""
    user_id = update.effective_user.id
    query_text = update.message.text.strip()
    
    with get_db_session() as db:
        # Отримуємо фільтри користувача (якщо є)
        filters = user_search_state.get(user_id, {})
        
        # Формуємо запит до БД
        db_query = db.query(JobListing).filter(JobListing.is_active == True)
        
        # Пошук за ключовими словами
        if query_text:
            search_filter = or_(
                JobListing.title.ilike(f"%{query_text}%"),
                JobListing.description.ilike(f"%{query_text}%"),
                JobListing.company.ilike(f"%{query_text}%")
            )
            db_query = db_query.filter(search_filter)
        
        # Застосовуємо фільтри
        if filters.get("city"):
            db_query = db_query.filter(JobListing.city == filters["city"])
        
        if filters.get("category"):
            db_query = db_query.filter(JobListing.category == filters["category"])
        
        if filters.get("employment_type"):
            db_query = db_query.filter(JobListing.employment_type == filters["employment_type"])
        
        if filters.get("salary_min"):
            db_query = db_query.filter(
                or_(
                    JobListing.salary_min >= filters["salary_min"],
                    JobListing.salary_max >= filters["salary_min"]
                )
            )
        
        # Сортуємо за датою публікації
        db_query = db_query.order_by(JobListing.published_date.desc())
        
        # Отримуємо результати
        jobs = db_query.limit(50).all()
        
        # Зберігаємо результати для пагінації
        user_search_state[user_id] = {
            **filters,
            "jobs": [job.id for job in jobs],
            "current_page": 1
        }
        
        # Зберігаємо в історію пошуку
        db_user = db.query(User).filter(User.telegram_id == user_id).first()
        if db_user:
            search_history = SearchHistory(
                user_id=db_user.id,
                query=query_text,
                filters=filters,
                results_count=len(jobs)
            )
            db.add(search_history)
            db.commit()
        
        if not jobs:
            await update.message.reply_text(
                MESSAGES["no_results"],
                reply_markup=get_back_to_menu_keyboard()
            )
            return
        
        # Показуємо перший результат
        await show_job_page(update, context, user_id, 1)


async def show_job_page(update: Update, context: ContextTypes.DEFAULT_TYPE, user_id: int, page: int):
    """Показує сторінку з вакансією"""
    state = user_search_state.get(user_id, {})
    job_ids = state.get("jobs", [])
    
    if not job_ids:
        await update.callback_query.answer("Немає результатів")
        return
    
    total_pages = len(job_ids)
    if page < 1 or page > total_pages:
        await update.callback_query.answer("Невірна сторінка")
        return
    
    with get_db_session() as db:
        job_id = job_ids[page - 1]
        job = db.query(JobListing).filter(JobListing.id == job_id).first()
        
        if not job:
            await update.callback_query.answer("Вакансія не знайдена")
            return
        
        # Перевіряємо чи в улюблених
        from database.models import UserFavorite
        db_user = db.query(User).filter(User.telegram_id == user_id).first()
        is_favorite = False
        if db_user:
            favorite = db.query(UserFavorite).filter(
                UserFavorite.user_id == db_user.id,
                UserFavorite.job_listing_id == job.id
            ).first()
            is_favorite = favorite is not None
        
        # Оновлюємо стан
        user_search_state[user_id]["current_page"] = page
        
        # Форматуємо та відправляємо
        text = format_job_listing(job)
        
        await update.callback_query.edit_message_text(
            text,
            reply_markup=get_pagination_keyboard(page, total_pages, job.id, is_favorite),
            parse_mode="HTML",
            disable_web_page_preview=False
        )


async def page_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обробник пагінації"""
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    data = query.data
    
    if data.startswith("page_"):
        page_num = int(data.split("_")[1])
        await show_job_page(update, context, user_id, page_num)
