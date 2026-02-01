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
    user_id = update.effective_user.id
    
    if update.callback_query:
        await update.callback_query.answer()
    
    with get_db_session() as db:
        # Отримуємо фільтри користувача
        state = user_search_state.get(user_id, {})
        filters_dict = state.get("filters", {})
        
        # Формуємо запит до БД
        db_query = db.query(JobListing).filter(JobListing.is_active == True)
        
        # Застосовуємо фільтри
        if filters_dict.get("city"):
            db_query = db_query.filter(JobListing.city == filters_dict["city"])
        
        if filters_dict.get("category"):
            db_query = db_query.filter(JobListing.category == filters_dict["category"])
        
        if filters_dict.get("employment_type"):
            db_query = db_query.filter(JobListing.employment_type == filters_dict["employment_type"])
        
        if filters_dict.get("salary_min"):
            try:
                s_min = float(filters_dict["salary_min"])
                db_query = db_query.filter(
                    or_(
                        JobListing.salary_min >= s_min,
                        JobListing.salary_max >= s_min
                    )
                )
            except (ValueError, TypeError):
                pass
        
        if filters_dict.get("keywords"):
            kws = [k.strip() for k in filters_dict["keywords"].split(",") if k.strip()]
            if kws:
                kw_filters = []
                for kw in kws:
                    kw_filters.append(
                        or_(
                            JobListing.title.ilike(f"%{kw}%"),
                            JobListing.description.ilike(f"%{kw}%")
                        )
                    )
                db_query = db_query.filter(and_(*kw_filters))

        # Отримуємо 3 випадкові (або просто перші) вакансії що відповідають фільтрам
        from sqlalchemy.sql import func
        jobs = db_query.order_by(func.random()).limit(10).all() # Більше ніж 3 для кращого вибору
        
        if jobs:
            # Зберігаємо результати для пагінації
            if user_id not in user_search_state:
                user_search_state[user_id] = {"filters": {}}
            
            user_search_state[user_id].update({
                "jobs": [job.id for job in jobs],
                "current_page": 1
            })
            
            # Показуємо першу вакансію
            await show_job_page(update, context, user_id, 1)
            return

    # Якщо вакансій немає або помилка
    text = "🔍 <b>Пошук вакансій</b>\n\nНа жаль, активних вакансій зараз немає. Спробуйте змінити фільтри або введіть запит вручну."
    
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
        # Отримуємо стан
        state = user_search_state.get(user_id, {"filters": {}})
        
        # Перевіряємо чи це введення для фільтрів
        waiting_for = state.get("waiting_for")
        if waiting_for:
            if waiting_for == "salary":
                try:
                    # Очищаємо текст від зайвого
                    salary_str = "".join(filter(str.isdigit, query_text))
                    if salary_str:
                        state["filters"]["salary_min"] = float(salary_str)
                        state.pop("waiting_for")
                        await update.message.reply_text(
                            f"✅ Мінімальну зарплату встановлено: {salary_str} PLN",
                            reply_markup=get_back_to_menu_keyboard()
                        )
                        return
                except ValueError:
                    pass
                await update.message.reply_text("❌ Будь ласка, введіть число (наприклад: 5000)")
                return
                
            elif waiting_for == "keywords":
                state["filters"]["keywords"] = query_text
                state.pop("waiting_for")
                await update.message.reply_text(
                    f"✅ Ключові слова встановлено: {query_text}",
                    reply_markup=get_back_to_menu_keyboard()
                )
                return

        # Формуємо запит до БД
        db_query = db.query(JobListing).filter(JobListing.is_active == True)
        
        # Пошук за ключовими словами з повідомлення
        if query_text:
            search_filter = or_(
                JobListing.title.ilike(f"%{query_text}%"),
                JobListing.description.ilike(f"%{query_text}%"),
                JobListing.company.ilike(f"%{query_text}%")
            )
            db_query = db_query.filter(search_filter)
        
        # Застосовуємо збережені фільтри
        filters_dict = state.get("filters", {})
        
        if filters_dict.get("city"):
            db_query = db_query.filter(JobListing.city == filters_dict["city"])
        
        if filters_dict.get("category"):
            db_query = db_query.filter(JobListing.category == filters_dict["category"])
        
        if filters_dict.get("employment_type"):
            db_query = db_query.filter(JobListing.employment_type == filters_dict["employment_type"])
        
        if filters_dict.get("salary_min"):
            s_min = filters_dict["salary_min"]
            db_query = db_query.filter(
                or_(
                    JobListing.salary_min >= s_min,
                    JobListing.salary_max >= s_min
                )
            )
            
        if filters_dict.get("keywords"):
             kws = [k.strip() for k in filters_dict["keywords"].split(",") if k.strip()]
             for kw in kws:
                db_query = db_query.filter(
                    or_(
                        JobListing.title.ilike(f"%{kw}%"),
                        JobListing.description.ilike(f"%{kw}%")
                    )
                )
        
        # Сортуємо за датою публікації
        db_query = db_query.order_by(JobListing.published_date.desc())
        
        # Отримуємо результати
        jobs = db_query.limit(50).all()
        
        # Зберігаємо результати для пагінації
        user_search_state[user_id] = {
            "filters": filters_dict,
            "jobs": [job.id for job in jobs],
            "current_page": 1
        }
        
        # Зберігаємо в історію пошуку
        db_user = db.query(User).filter(User.telegram_id == user_id).first()
        if db_user:
            search_history = SearchHistory(
                user_id=db_user.id,
                query=query_text,
                filters=filters_dict,
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
    
    if update.callback_query:
        try:
            await update.callback_query.answer()
        except Exception:
            pass # Ignore if already answered or too old

    if not job_ids:
        # Спробуємо відновити стан (наприклад, після перезапуску бота)
        with get_db_session() as db:
            from sqlalchemy.sql import func
            jobs = db.query(JobListing).filter(JobListing.is_active == True).order_by(func.random()).limit(3).all()
            if jobs:
                job_ids = [job.id for job in jobs]
                user_search_state[user_id] = {
                    "jobs": job_ids,
                    "current_page": 1,
                    "filters": {}
                }
                total_pages = len(job_ids)
                if page > total_pages:
                    page = 1
            else:
                if update.callback_query:
                    await update.callback_query.answer("Сесію пошуку завершено. Почніть новий пошук.")
                return
    
    total_pages = len(job_ids)
    if page < 1 or page > total_pages:
        if update.callback_query:
            await update.callback_query.answer("Невірна сторінка")
        return
    
    with get_db_session() as db:
        job_id = job_ids[page - 1]
        job = db.query(JobListing).filter(JobListing.id == job_id).first()
        
        if not job:
            if update.callback_query:
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
        
        keyboard = get_pagination_keyboard(page, total_pages, job.id, is_favorite)
        
        # Handle message editing vs sending new message
        if update.callback_query:
             await update.callback_query.edit_message_text(
                text,
                reply_markup=keyboard,
                parse_mode="HTML",
                disable_web_page_preview=False
            )
        else:
            # If triggered by text message (not callback), send existing message
            await update.message.reply_text(
                text,
                reply_markup=keyboard,
                parse_mode="HTML",
                disable_web_page_preview=False
            )


async def page_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обробник пагінації"""
    query = update.callback_query
    
    user_id = update.effective_user.id
    data = query.data
    
    import logging
    logger = logging.getLogger(__name__)
    logger.info(f"Callback received: {data} from user {user_id}")
    
    if data == "page_info":
        await query.answer("Використовуйте стрілки для навігації")
        return
        
    await query.answer()
    
    if data.startswith("page_"):
        try:
            page_num = int(data.split("_")[1])
            await show_job_page(update, context, user_id, page_num)
        except (ValueError, IndexError) as e:
            logger.error(f"Error parsing page number from {data}: {e}")
            await query.answer("Помилка пагінації")
