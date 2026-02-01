# 🔍 Аналіз коду WorkSearchBot

## 🔒 БЕЗПЕКА (Security Vulnerabilities)

### 1. SQL Injection через ILIKE запити ❌ КРИТИЧНО

**Проблема:** У файлі `bot/handlers/search.py` (рядки 64, 65, 148-152, 179-183) використовується небезпечна конкатенація рядків для ILIKE запитів.

**Вразливість:**
```python
# НЕБЕЗПЕЧНО - SQL Injection
JobListing.title.ilike(f"%{kw}%")
JobListing.description.ilike(f"%{query_text}%")
```

**Виправлення:**
```python
# БЕЗПЕЧНО - SQLAlchemy автоматично екранує параметри
from sqlalchemy import func

# Замість:
JobListing.title.ilike(f"%{kw}%")

# Використовуйте:
JobListing.title.ilike("%" + kw + "%")  # SQLAlchemy безпечно обробляє це

# Або для більш складних випадків:
from sqlalchemy import bindparam
db_query = db_query.filter(
    JobListing.title.op('ILIKE')(bindparam('keyword'))
).params(keyword=f"%{kw}%")
```

---

### 2. Відсутність валідації користувацького вводу ❌ ВИСОКИЙ РИЗИК

**Проблема:** У файлі `config/settings.py` (рядок 32) відсутня валідація формату для `ADMIN_USER_IDS`.

**Вразливість:**
```python
# НЕБЕЗПЕЧНО - може викликати ValueError
return [int(uid.strip()) for uid in self.ADMIN_USER_IDS.split(",") if uid.strip().isdigit()]
```

**Виправлення:**
```python
# БЕЗПЕЧНО
@property
def admin_ids_list(self) -> List[int]:
    """Повертає список ID адмінів з валідацією"""
    if not self.ADMIN_USER_IDS:
        return []
    
    result = []
    for uid in self.ADMIN_USER_IDS.split(","):
        uid = uid.strip()
        if uid.isdigit():
            try:
                user_id = int(uid)
                # Валідація діапазону Telegram ID (позитивні числа до 2^63)
                if 0 < user_id < 2**63:
                    result.append(user_id)
                else:
                    logger.warning(f"Invalid admin ID (out of range): {uid}")
            except (ValueError, OverflowError) as e:
                logger.warning(f"Invalid admin ID: {uid}, error: {e}")
    return result
```

---

### 3. Відкритий доступ до секретних токенів ❌ КРИТИЧНО

**Проблема:** У файлі `config/settings.py` (рядок 49) використовується TELEGRAM_BOT_TOKEN як fallback для WEBHOOK_SECRET_TOKEN.

**Вразливість:**
```python
# НЕБЕЗПЕЧНО - токен бота використовується як секрет
WEBHOOK_SECRET_TOKEN: str = os.getenv("WEBHOOK_SECRET_TOKEN", TELEGRAM_BOT_TOKEN)
```

**Виправлення:**
```python
# БЕЗПЕЧНО - генеруємо унікальний секрет
import secrets

WEBHOOK_SECRET_TOKEN: str = os.getenv(
    "WEBHOOK_SECRET_TOKEN", 
    secrets.token_urlsafe(32)  # Генеруємо випадковий токен
)

# Або у випадку якщо потрібно зберегти для рестарту:
@property
def webhook_secret_token(self) -> str:
    token = os.getenv("WEBHOOK_SECRET_TOKEN")
    if not token:
        token = secrets.token_urlsafe(32)
        logger.warning("WEBHOOK_SECRET_TOKEN not set, generated: Store this in .env file!")
        logger.info(f"Add to .env: WEBHOOK_SECRET_TOKEN={token}")
    return token
```

---

### 4. Відсутність rate limiting на рівні користувача ⚠️ СЕРЕДНІЙ РИЗИК

**Проблема:** У файлі `config/settings.py` визначені ліміти, але вони не використовуються в коді.

**Виправлення:** Додайте middleware для rate limiting:

```python
# bot/middlewares/rate_limit.py
from telegram import Update
from telegram.ext import ContextTypes
from datetime import datetime, timedelta
from collections import defaultdict
import logging

logger = logging.getLogger(__name__)

class RateLimiter:
    def __init__(self, max_requests: int = 30, time_window: int = 60):
        self.max_requests = max_requests
        self.time_window = timedelta(seconds=time_window)
        self.user_requests = defaultdict(list)
    
    def is_allowed(self, user_id: int) -> bool:
        now = datetime.now()
        
        # Видаляємо старі запити
        self.user_requests[user_id] = [
            req_time for req_time in self.user_requests[user_id]
            if now - req_time < self.time_window
        ]
        
        # Перевіряємо ліміт
        if len(self.user_requests[user_id]) >= self.max_requests:
            return False
        
        self.user_requests[user_id].append(now)
        return True

# Використання в main.py:
rate_limiter = RateLimiter(
    max_requests=settings.MAX_REQUESTS_PER_MINUTE,
    time_window=60
)

async def rate_limit_middleware(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    if not rate_limiter.is_allowed(user_id):
        await update.message.reply_text(
            "⚠️ Занадто багато запитів. Зачекайте хвилину."
        )
        return  # Блокуємо виконання
    
    # Продовжуємо обробку
    return await context.dispatcher.process_update(update)
```

---

### 5. Потенційна DoS через необмежений запит до БД ⚠️ СЕРЕДНІЙ РИЗИК

**Проблема:** У файлі `bot/handlers/search.py` (рядок 190) запит обмежений тільки 50 результатами, але немає обмеження на складність запиту.

**Виправлення:**
```python
# Додайте таймаут та обмеження для складних запитів
from sqlalchemy import event
from sqlalchemy.engine import Engine
import time

# В database.py додайте:
@event.listens_for(Engine, "before_cursor_execute")
def receive_before_cursor_execute(conn, cursor, statement, params, context, executemany):
    conn.info.setdefault('query_start_time', []).append(time.time())

@event.listens_for(Engine, "after_cursor_execute")
def receive_after_cursor_execute(conn, cursor, statement, params, context, executemany):
    total = time.time() - conn.info['query_start_time'].pop(-1)
    if total > 5.0:  # Більше 5 секунд
        logger.warning(f"Slow query detected: {total:.2f}s - {statement[:100]}")

# У search.py додайте обмеження:
MAX_KEYWORDS = 5
MAX_KEYWORD_LENGTH = 100

if filters_dict.get("keywords"):
    kws = [k.strip()[:MAX_KEYWORD_LENGTH] for k in filters_dict["keywords"].split(",") if k.strip()]
    kws = kws[:MAX_KEYWORDS]  # Обмежуємо кількість ключових слів
```

---

### 6. Небезпечне використання eval/exec відсутнє ✅ ДОБРЕ

**Статус:** У коді не знайдено використання eval() або exec(), що є гарною практикою.

---

### 7. Логування чутливої інформації ⚠️ СЕРЕДНІЙ РИЗИК

**Проблема:** У файлі `database/database.py` (рядок 40) логується URL бази даних, який може містити пароль.

**Вразливість:**
```python
# НЕБЕЗПЕЧНО - може логувати пароль
safe_url = db_url.split('@')[-1] if '@' in db_url else db_url
logger.info(f"Ініціалізація бази даних: {safe_url}")
```

**Виправлення:**
```python
# БЕЗПЕЧНО - маскуємо всю чутливу інформацію
from urllib.parse import urlparse, urlunparse

def sanitize_db_url(url: str) -> str:
    """Видаляє чутливу інформацію з URL бази даних"""
    try:
        parsed = urlparse(url)
        # Замінюємо пароль на зірочки
        if parsed.password:
            netloc = f"{parsed.username}:***@{parsed.hostname}"
            if parsed.port:
                netloc += f":{parsed.port}"
            sanitized = parsed._replace(netloc=netloc)
            return urlunparse(sanitized)
        return url.replace(parsed.password or "", "***") if parsed.password else url
    except Exception:
        return "***"  # У випадку помилки приховуємо все

logger.info(f"Ініціалізація бази даних: {sanitize_db_url(db_url)}")
```

---

## ⚡ ПРОДУКТИВНІСТЬ (Performance Bottlenecks)

### 1. N+1 Query Problem ❌ КРИТИЧНИЙ ВПЛИВ

**Проблема:** У файлі `bot/handlers/search.py` (рядки 269-277) виконується додатковий запит до БД для кожної вакансії.

**Неефективно:**
```python
# Виконується 2 запити для кожної вакансії
job = db.query(JobListing).filter(JobListing.id == job_id).first()
db_user = db.query(User).filter(User.telegram_id == user_id).first()
favorite = db.query(UserFavorite).filter(...).first()
```

**Оптимізація:**
```python
# Один запит з JOIN
from sqlalchemy.orm import joinedload

# Завантажуємо все за один запит
job = db.query(JobListing).options(
    joinedload(JobListing.favorites)
).filter(JobListing.id == job_id).first()

# Кешуємо user об'єкт
if not hasattr(context, 'cached_user'):
    context.cached_user = db.query(User).filter(
        User.telegram_id == user_id
    ).first()
db_user = context.cached_user

# Перевіряємо чи в улюблених через завантажені дані
is_favorite = any(fav.user_id == db_user.id for fav in job.favorites) if db_user else False
```

---

### 2. Відсутність індексів на часто використовуваних полях ❌ ВИСОКИЙ ВПЛИВ

**Проблема:** У файлі `database/models.py` відсутні складені індекси для складних запитів.

**Оптимізація:**
```python
# database/models.py - додайте складені індекси

from sqlalchemy import Index

class JobListing(Base):
    __tablename__ = "job_listings"
    
    # ... існуючі поля ...
    
    # Додайте складені індекси
    __table_args__ = (
        # Для пошуку з фільтрами
        Index('idx_active_city_category', 'is_active', 'city', 'category'),
        Index('idx_active_published', 'is_active', 'published_date'),
        Index('idx_source_active', 'source', 'is_active'),
        # Для full-text search (PostgreSQL)
        # Index('idx_title_gin', 'title', postgresql_using='gin', postgresql_ops={'title': 'gin_trgm_ops'}),
    )

class SearchHistory(Base):
    __tablename__ = "search_history"
    
    # ... існуючі поля ...
    
    __table_args__ = (
        Index('idx_user_created', 'user_id', 'created_at'),
    )
```

**Міграція для додавання індексів:**
```bash
# Створіть міграцію:
alembic revision -m "Add composite indexes for performance"
```

```python
# У файлі міграції:
def upgrade():
    op.create_index('idx_active_city_category', 'job_listings', ['is_active', 'city', 'category'])
    op.create_index('idx_active_published', 'job_listings', ['is_active', 'published_date'])
    op.create_index('idx_source_active', 'job_listings', ['source', 'is_active'])
    op.create_index('idx_user_created', 'search_history', ['user_id', 'created_at'])

def downgrade():
    op.drop_index('idx_user_created', 'search_history')
    op.drop_index('idx_source_active', 'job_listings')
    op.drop_index('idx_active_published', 'job_listings')
    op.drop_index('idx_active_city_category', 'job_listings')
```

---

### 3. Синхронний скрапінг блокує event loop ❌ ВИСОКИЙ ВПЛИВ

**Проблема:** У файлі `scraper/base_scraper.py` (рядки 25-43) синхронні HTTP запити блокують event loop.

**Неефективно:**
```python
# Блокуючий синхронний запит
response = self.session.get(url, timeout=30)
time.sleep(random.uniform(2, 5))  # Блокує весь event loop!
```

**Оптимізація:**
```python
# scraper/base_scraper.py
import aiohttp
import asyncio

class BaseScraper(ABC):
    def __init__(self, source_name: str, base_url: str):
        self.source_name = source_name
        self.base_url = base_url
        self.headers = {'User-Agent': settings.USER_AGENT}
    
    async def fetch_page(self, url: str, retries: int = 3) -> Optional[str]:
        """Асинхронно отримує HTML сторінку"""
        async with aiohttp.ClientSession(headers=self.headers) as session:
            for attempt in range(retries):
                try:
                    async with session.get(url, timeout=aiohttp.ClientTimeout(total=30)) as response:
                        response.raise_for_status()
                        
                        # Асинхронна затримка - не блокує event loop
                        await asyncio.sleep(random.uniform(2, 5))
                        
                        return await response.text()
                except Exception as e:
                    logger.warning(f"Помилка при отриманні {url} (спроба {attempt + 1}/{retries}): {e}")
                    if attempt < retries - 1:
                        await asyncio.sleep(2 ** attempt)
                    else:
                        logger.error(f"Не вдалося отримати {url} після {retries} спроб")
        return None
    
    @abstractmethod
    async def fetch_jobs(self, max_pages: int = 5) -> List[Dict]:
        """Асинхронно отримує список вакансій"""
        pass
```

---

### 4. Відсутність кешування для часто запитуваних даних ⚠️ СЕРЕДНІЙ ВПЛИВ

**Проблема:** Кожен запит виконує SQL запити, навіть для статичних даних.

**Оптимізація:**
```python
# bot/utils/cache.py
from functools import lru_cache
from datetime import datetime, timedelta
import redis
from config import settings
import json
import pickle

class Cache:
    def __init__(self):
        if settings.REDIS_URL:
            self.redis_client = redis.from_url(settings.REDIS_URL)
            self.use_redis = True
        else:
            self.use_redis = False
            self._local_cache = {}
    
    def get(self, key: str):
        """Отримати значення з кешу"""
        if self.use_redis:
            value = self.redis_client.get(key)
            return pickle.loads(value) if value else None
        return self._local_cache.get(key)
    
    def set(self, key: str, value, ttl: int = 300):
        """Зберегти значення в кеш з TTL (секунди)"""
        if self.use_redis:
            self.redis_client.setex(key, ttl, pickle.dumps(value))
        else:
            self._local_cache[key] = value
            # Для локального кешу можна додати логіку видалення через TTL
    
    def delete(self, key: str):
        """Видалити значення з кешу"""
        if self.use_redis:
            self.redis_client.delete(key)
        else:
            self._local_cache.pop(key, None)

cache = Cache()

# Використання в search.py:
def get_user_cached(db: Session, telegram_id: int):
    cache_key = f"user:{telegram_id}"
    user = cache.get(cache_key)
    
    if not user:
        user = db.query(User).filter(User.telegram_id == telegram_id).first()
        if user:
            cache.set(cache_key, user, ttl=300)  # 5 хвилин
    
    return user

# Для статистики міст:
@lru_cache(maxsize=1)
def get_cities_list():
    """Кешує список міст в пам'яті"""
    from config.constants import POLISH_CITIES
    return POLISH_CITIES
```

---

### 5. Неоптимізоване завантаження великих результатів ⚠️ СЕРЕДНІЙ ВПЛИВ

**Проблема:** У файлі `bot/handlers/search.py` (рядок 190) завантажується 50 результатів одразу в пам'ять.

**Оптимізація:**
```python
# Пагінація на рівні БД з курсорами
def search_jobs_paginated(db: Session, filters: dict, page: int = 1, per_page: int = 10):
    """Оптимізований пошук з пагінацією"""
    offset = (page - 1) * per_page
    
    query = db.query(JobListing.id).filter(JobListing.is_active == True)
    
    # Застосовуємо фільтри...
    
    # Отримуємо тільки ID для пагінації (набагато швидше)
    total_count = query.count()  # Кешуйте це значення
    job_ids = query.order_by(JobListing.published_date.desc())\
                   .offset(offset)\
                   .limit(per_page)\
                   .all()
    
    return [job_id[0] for job_id in job_ids], total_count

# Використання:
job_ids, total = search_jobs_paginated(db, filters_dict, page=1, per_page=10)
user_search_state[user_id] = {
    "filters": filters_dict,
    "jobs": job_ids,  # Тільки ID, не повні об'єкти
    "total": total,
    "current_page": 1
}
```

---

### 6. Пам'ять витікає через user_search_state ⚠️ СЕРЕДНІЙ ВПЛИВ

**Проблема:** У файлі `bot/handlers/search.py` (рядок 16) глобальний словник `user_search_state` ніколи не очищається.

**Оптимізація:**
```python
# bot/handlers/search.py
from collections import OrderedDict
from datetime import datetime

class SearchStateManager:
    def __init__(self, max_size: int = 1000, ttl_seconds: int = 3600):
        self.states = OrderedDict()
        self.max_size = max_size
        self.ttl_seconds = ttl_seconds
    
    def get(self, user_id: int, default=None):
        """Отримати стан з перевіркою TTL"""
        if user_id in self.states:
            state, timestamp = self.states[user_id]
            if (datetime.now() - timestamp).total_seconds() < self.ttl_seconds:
                return state
            else:
                del self.states[user_id]
        return default
    
    def set(self, user_id: int, state):
        """Зберегти стан з автоматичним очищенням"""
        self.states[user_id] = (state, datetime.now())
        self.states.move_to_end(user_id)
        
        # Видаляємо найстаріші записи якщо перевищено ліміт
        while len(self.states) > self.max_size:
            self.states.popitem(last=False)

# Замість глобального словника:
user_search_state_manager = SearchStateManager(max_size=1000, ttl_seconds=3600)

# Використання:
state = user_search_state_manager.get(user_id, {"filters": {}})
```

---

## 🚀 НОВІ ФІЧІ (Feature Suggestions)

### 1. Автоматичні сповіщення про нові вакансії за підписками

**Опис:** Реалізувати функціонал відправки сповіщень користувачам про нові вакансії, що відповідають їх підпискам.

**Реалізація:**
```python
# bot/jobs/subscription_notifier.py
from telegram import Bot
from database.database import get_db
from database.models import UserSubscription, JobListing, User
from sqlalchemy.orm import Session
from sqlalchemy import and_
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

async def check_subscriptions_and_notify(bot: Bot):
    """Перевіряє підписки та відправляє сповіщення"""
    db_gen = get_db()
    db: Session = next(db_gen)
    
    try:
        # Отримуємо активні підписки
        subscriptions = db.query(UserSubscription).filter(
            UserSubscription.is_active == True
        ).all()
        
        for subscription in subscriptions:
            try:
                # Знаходимо нові вакансії (за останню годину)
                query = db.query(JobListing).filter(
                    and_(
                        JobListing.is_active == True,
                        JobListing.scraped_at >= datetime.utcnow() - timedelta(hours=1)
                    )
                )
                
                # Застосовуємо фільтри підписки
                if subscription.city:
                    query = query.filter(JobListing.city == subscription.city)
                
                if subscription.category:
                    query = query.filter(JobListing.category == subscription.category)
                
                if subscription.salary_min:
                    query = query.filter(
                        JobListing.salary_min >= subscription.salary_min
                    )
                
                if subscription.keywords:
                    import json
                    keywords = json.loads(subscription.keywords)
                    for keyword in keywords:
                        query = query.filter(
                            JobListing.title.ilike(f"%{keyword}%")
                        )
                
                new_jobs = query.limit(5).all()
                
                if new_jobs:
                    # Відправляємо сповіщення
                    user = subscription.user
                    message = f"🔔 <b>Нові вакансії за вашою підпискою!</b>\n\n"
                    
                    for job in new_jobs:
                        message += f"📌 <b>{job.title}</b>\n"
                        message += f"🏢 {job.company or 'Не вказано'}\n"
                        message += f"📍 {job.location or job.city}\n"
                        if job.salary_min:
                            message += f"💰 від {job.salary_min} {job.salary_currency}\n"
                        message += f"🔗 {job.url}\n\n"
                    
                    await bot.send_message(
                        chat_id=user.telegram_id,
                        text=message,
                        parse_mode="HTML",
                        disable_web_page_preview=True
                    )
                    
                    logger.info(f"Sent {len(new_jobs)} new jobs to user {user.telegram_id}")
                    
            except Exception as e:
                logger.error(f"Error processing subscription {subscription.id}: {e}")
                continue
    
    finally:
        try:
            next(db_gen, None)
        except StopIteration:
            pass

# Додайте в main.py:
from bot.jobs.subscription_notifier import check_subscriptions_and_notify

async def post_init(application: Application):
    """Виконується після ініціалізації бота"""
    logger.info("Бот ініціалізовано")
    
    # Запускаємо планувальник скрапінгу
    if settings.SCRAPING_ENABLED:
        scheduler = ScrapingScheduler()
        scheduler.start()
        application.bot_data['scheduler'] = scheduler
    
    # Додаємо задачу для сповіщень про підписки
    job_queue = application.job_queue
    job_queue.run_repeating(
        lambda context: check_subscriptions_and_notify(context.bot),
        interval=3600,  # Кожну годину
        first=60  # Перший запуск через 1 хвилину
    )
```

---

### 2. Аналітика та рекомендації на основі історії пошуку

**Опис:** Додати персоналізовані рекомендації вакансій на основі історії пошуків користувача.

**Реалізація:**
```python
# bot/utils/recommendations.py
from database.models import SearchHistory, JobListing, User
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from collections import Counter
from typing import List
import json

def get_user_recommendations(db: Session, user: User, limit: int = 10) -> List[JobListing]:
    """Отримує рекомендовані вакансії на основі історії"""
    
    # Аналізуємо історію пошуку користувача (за останній місяць)
    from datetime import datetime, timedelta
    one_month_ago = datetime.utcnow() - timedelta(days=30)
    
    history = db.query(SearchHistory).filter(
        SearchHistory.user_id == user.id,
        SearchHistory.created_at >= one_month_ago
    ).all()
    
    if not history:
        # Якщо немає історії, повертаємо популярні вакансії
        return get_popular_jobs(db, limit)
    
    # Збираємо інтереси користувача
    all_queries = []
    all_cities = []
    all_categories = []
    
    for entry in history:
        if entry.query:
            all_queries.append(entry.query.lower())
        
        if entry.filters:
            if isinstance(entry.filters, str):
                filters = json.loads(entry.filters)
            else:
                filters = entry.filters
            
            if filters.get('city'):
                all_cities.append(filters['city'])
            if filters.get('category'):
                all_categories.append(filters['category'])
    
    # Знаходимо найчастіші інтереси
    query_counter = Counter(all_queries)
    city_counter = Counter(all_cities)
    category_counter = Counter(all_categories)
    
    top_queries = [q for q, _ in query_counter.most_common(3)]
    top_city = city_counter.most_common(1)[0][0] if all_cities else None
    top_category = category_counter.most_common(1)[0][0] if all_categories else None
    
    # Формуємо запит для рекомендацій
    query = db.query(JobListing).filter(JobListing.is_active == True)
    
    # Пріоритет 1: місто та категорія
    if top_city and top_category:
        query = query.filter(
            JobListing.city == top_city,
            JobListing.category == top_category
        )
    elif top_city:
        query = query.filter(JobListing.city == top_city)
    elif top_category:
        query = query.filter(JobListing.category == top_category)
    
    # Пріоритет 2: ключові слова
    if top_queries:
        from sqlalchemy import or_
        keyword_filters = []
        for kw in top_queries:
            keyword_filters.append(JobListing.title.ilike(f"%{kw}%"))
            keyword_filters.append(JobListing.description.ilike(f"%{kw}%"))
        query = query.filter(or_(*keyword_filters))
    
    # Сортуємо за новизною
    jobs = query.order_by(desc(JobListing.published_date)).limit(limit).all()
    
    return jobs

def get_popular_jobs(db: Session, limit: int = 10) -> List[JobListing]:
    """Повертає популярні вакансії (найбільше переглядів)"""
    # Можна додати поле views до моделі JobListing
    return db.query(JobListing).filter(
        JobListing.is_active == True
    ).order_by(desc(JobListing.published_date)).limit(limit).all()

# Додайте handler:
# bot/handlers/recommendations.py
from bot.utils.recommendations import get_user_recommendations
from bot.keyboards.main_menu import get_back_to_menu_keyboard
from bot.utils.formatters import format_job_listing

async def recommendations_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обробник команди /recommendations"""
    user_id = update.effective_user.id
    
    with get_db_session() as db:
        db_user = db.query(User).filter(User.telegram_id == user_id).first()
        
        if not db_user:
            await update.message.reply_text(
                "❌ Користувача не знайдено. Використайте /start"
            )
            return
        
        jobs = get_user_recommendations(db, db_user, limit=10)
        
        if not jobs:
            await update.message.reply_text(
                "📊 Поки що немає рекомендацій. Спробуйте пошукати вакансії!",
                reply_markup=get_back_to_menu_keyboard()
            )
            return
        
        # Зберігаємо для пагінації
        user_search_state[user_id] = {
            "jobs": [job.id for job in jobs],
            "current_page": 1,
            "filters": {}
        }
        
        await show_job_page(update, context, user_id, 1)
```

---

### 3. Експорт вакансій у PDF/Excel

**Опис:** Дозволити користувачам експортувати знайдені вакансії або обрані в PDF або Excel форматі.

**Реалізація:**
```python
# bot/utils/export.py
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
from reportlab.lib.units import inch
import io
from typing import List
from database.models import JobListing
import pandas as pd

def export_jobs_to_pdf(jobs: List[JobListing]) -> io.BytesIO:
    """Експортує вакансії у PDF"""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    styles = getSampleStyleSheet()
    story = []
    
    # Заголовок
    title = Paragraph("Вакансії WorkSearchBot", styles['Title'])
    story.append(title)
    story.append(Spacer(1, 0.2*inch))
    
    for job in jobs:
        # Назва вакансії
        job_title = Paragraph(f"<b>{job.title}</b>", styles['Heading2'])
        story.append(job_title)
        
        # Деталі
        details = f"""
        <b>Компанія:</b> {job.company or 'Не вказано'}<br/>
        <b>Локація:</b> {job.location or job.city or 'Не вказано'}<br/>
        """
        
        if job.salary_min or job.salary_max:
            salary_text = f"від {job.salary_min}" if job.salary_min else ""
            if job.salary_max:
                salary_text += f" до {job.salary_max}"
            salary_text += f" {job.salary_currency}"
            details += f"<b>Зарплата:</b> {salary_text}<br/>"
        
        details += f"<b>Посилання:</b> {job.url}<br/>"
        
        details_p = Paragraph(details, styles['Normal'])
        story.append(details_p)
        
        # Опис
        if job.description:
            desc_text = job.description[:500] + "..." if len(job.description) > 500 else job.description
            desc = Paragraph(f"<b>Опис:</b> {desc_text}", styles['Normal'])
            story.append(desc)
        
        story.append(Spacer(1, 0.3*inch))
    
    doc.build(story)
    buffer.seek(0)
    return buffer

def export_jobs_to_excel(jobs: List[JobListing]) -> io.BytesIO:
    """Експортує вакансії у Excel"""
    data = []
    
    for job in jobs:
        data.append({
            'Назва': job.title,
            'Компанія': job.company or 'Не вказано',
            'Локація': job.location or job.city,
            'Місто': job.city,
            'Мін. зарплата': job.salary_min,
            'Макс. зарплата': job.salary_max,
            'Валюта': job.salary_currency,
            'Тип зайнятості': job.employment_type,
            'Категорія': job.category,
            'Посилання': job.url,
            'Дата публікації': job.published_date.strftime('%Y-%m-%d') if job.published_date else ''
        })
    
    df = pd.DataFrame(data)
    buffer = io.BytesIO()
    
    with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Вакансії')
        
        # Автоматичне налаштування ширини колонок
        worksheet = writer.sheets['Вакансії']
        for i, col in enumerate(df.columns):
            max_length = max(df[col].astype(str).apply(len).max(), len(col)) + 2
            worksheet.set_column(i, i, min(max_length, 50))
    
    buffer.seek(0)
    return buffer

# bot/handlers/export.py
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes
from bot.utils.export import export_jobs_to_pdf, export_jobs_to_excel
from database.models import JobListing, UserFavorite, User

async def export_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обробник команди /export"""
    keyboard = [
        [
            InlineKeyboardButton("📄 PDF", callback_data="export_pdf"),
            InlineKeyboardButton("📊 Excel", callback_data="export_excel")
        ],
        [InlineKeyboardButton("« Назад", callback_data="main_menu")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    text = "📤 <b>Експорт вакансій</b>\n\nОберіть формат для експорту ваших обраних вакансій:"
    
    if update.callback_query:
        await update.callback_query.edit_message_text(
            text,
            reply_markup=reply_markup,
            parse_mode="HTML"
        )
    else:
        await update.message.reply_text(
            text,
            reply_markup=reply_markup,
            parse_mode="HTML"
        )

async def export_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обробник callbacks для експорту"""
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    
    with get_db_session() as db:
        db_user = db.query(User).filter(User.telegram_id == user_id).first()
        
        if not db_user:
            await query.edit_message_text("❌ Користувача не знайдено")
            return
        
        # Отримуємо обрані вакансії
        favorites = db.query(UserFavorite).filter(
            UserFavorite.user_id == db_user.id
        ).all()
        
        if not favorites:
            await query.edit_message_text(
                "❌ У вас немає обраних вакансій для експорту.\n"
                "Спочатку додайте вакансії до обраних."
            )
            return
        
        jobs = [fav.job_listing for fav in favorites]
        
        await query.edit_message_text("⏳ Генерую файл...")
        
        try:
            if query.data == "export_pdf":
                buffer = export_jobs_to_pdf(jobs)
                filename = f"vacancies_{user_id}.pdf"
                
                await context.bot.send_document(
                    chat_id=user_id,
                    document=buffer,
                    filename=filename,
                    caption=f"📄 Ваші обрані вакансії ({len(jobs)} шт.)"
                )
            
            elif query.data == "export_excel":
                buffer = export_jobs_to_excel(jobs)
                filename = f"vacancies_{user_id}.xlsx"
                
                await context.bot.send_document(
                    chat_id=user_id,
                    document=buffer,
                    filename=filename,
                    caption=f"📊 Ваші обрані вакансії ({len(jobs)} шт.)"
                )
            
            await query.message.reply_text("✅ Файл успішно згенеровано!")
            
        except Exception as e:
            logger.error(f"Error exporting: {e}")
            await query.message.reply_text("❌ Помилка при експорті файлу")

# Додайте в requirements.txt:
# reportlab==4.0.7
# pandas==2.1.3
# openpyxl==3.1.2
# xlsxwriter==3.1.9
```

---

### 4. Розширений пошук з AI/ML підтримкою

**Опис:** Використання NLP для покращення релевантності пошуку та автоматичної категоризації вакансій.

**Реалізація:**
```python
# bot/utils/ai_search.py
from typing import List, Dict
from database.models import JobListing
from sqlalchemy.orm import Session

# Використовуємо sentence-transformers для семантичного пошуку
try:
    from sentence_transformers import SentenceTransformer, util
    import torch
    AI_SEARCH_AVAILABLE = True
except ImportError:
    AI_SEARCH_AVAILABLE = False

class AIJobSearcher:
    def __init__(self):
        if not AI_SEARCH_AVAILABLE:
            raise ImportError("Install sentence-transformers: pip install sentence-transformers")
        
        # Завантажуємо модель (можна використати multilingual модель)
        self.model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')
        self.job_embeddings_cache = {}
    
    def encode_jobs(self, jobs: List[JobListing]) -> Dict[int, torch.Tensor]:
        """Створює векторні представлення для вакансій"""
        embeddings = {}
        
        for job in jobs:
            if job.id in self.job_embeddings_cache:
                embeddings[job.id] = self.job_embeddings_cache[job.id]
                continue
            
            # Комбінуємо назву, опис та компанію
            text = f"{job.title}. {job.description or ''}. {job.company or ''}"
            embedding = self.model.encode(text, convert_to_tensor=True)
            
            embeddings[job.id] = embedding
            self.job_embeddings_cache[job.id] = embedding
        
        return embeddings
    
    def semantic_search(self, query: str, jobs: List[JobListing], top_k: int = 10) -> List[JobListing]:
        """Семантичний пошук вакансій"""
        if not jobs:
            return []
        
        # Кодуємо запит
        query_embedding = self.model.encode(query, convert_to_tensor=True)
        
        # Кодуємо вакансії
        job_embeddings = self.encode_jobs(jobs)
        
        # Обчислюємо подібність
        job_ids = list(job_embeddings.keys())
        embeddings_tensor = torch.stack([job_embeddings[jid] for jid in job_ids])
        
        cos_scores = util.cos_sim(query_embedding, embeddings_tensor)[0]
        
        # Сортуємо за релевантністю
        top_results = torch.topk(cos_scores, k=min(top_k, len(jobs)))
        
        # Повертаємо найрелевантніші вакансії
        result_jobs = [jobs[idx] for idx in top_results.indices]
        
        return result_jobs

# Інтеграція в search.py:
ai_searcher = AIJobSearcher() if AI_SEARCH_AVAILABLE else None

async def ai_search_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обробник AI пошуку"""
    if not AI_SEARCH_AVAILABLE:
        await update.message.reply_text(
            "❌ AI пошук недоступний. Встановіть залежності:\n"
            "pip install sentence-transformers torch"
        )
        return
    
    query_text = update.message.text.strip()
    user_id = update.effective_user.id
    
    with get_db_session() as db:
        # Отримуємо всі активні вакансії (або з фільтрами)
        jobs = db.query(JobListing).filter(
            JobListing.is_active == True
        ).limit(100).all()  # Обмежуємо для продуктивності
        
        if not jobs:
            await update.message.reply_text("❌ Немає активних вакансій")
            return
        
        await update.message.reply_text("🤖 Шукаю найкращі збіги за допомогою AI...")
        
        # Виконуємо семантичний пошук
        import asyncio
        relevant_jobs = await asyncio.to_thread(
            ai_searcher.semantic_search,
            query_text,
            jobs,
            top_k=10
        )
        
        # Зберігаємо результати
        user_search_state[user_id] = {
            "jobs": [job.id for job in relevant_jobs],
            "current_page": 1,
            "filters": {}
        }
        
        await show_job_page(update, context, user_id, 1)

# Додайте в requirements.txt:
# sentence-transformers==2.2.2
# torch==2.1.0
```

---

### 5. Telegram Web App інтеграція

**Опис:** Створити Web App для більш зручного інтерфейсу пошуку та перегляду вакансій.

**Реалізація:**
```python
# bot/webapp/app.py
from flask import Flask, render_template, request, jsonify
from database.database import get_db
from database.models import JobListing
from sqlalchemy import or_

app = Flask(__name__)

@app.route('/')
def index():
    """Головна сторінка Web App"""
    return render_template('index.html')

@app.route('/api/search')
def api_search():
    """API для пошуку вакансій"""
    query = request.args.get('q', '')
    city = request.args.get('city', '')
    category = request.args.get('category', '')
    page = int(request.args.get('page', 1))
    per_page = 20
    
    db_gen = get_db()
    db = next(db_gen)
    
    try:
        db_query = db.query(JobListing).filter(JobListing.is_active == True)
        
        if query:
            db_query = db_query.filter(
                or_(
                    JobListing.title.ilike(f"%{query}%"),
                    JobListing.description.ilike(f"%{query}%")
                )
            )
        
        if city:
            db_query = db_query.filter(JobListing.city == city)
        
        if category:
            db_query = db_query.filter(JobListing.category == category)
        
        total = db_query.count()
        jobs = db_query.offset((page - 1) * per_page).limit(per_page).all()
        
        return jsonify({
            'jobs': [
                {
                    'id': job.id,
                    'title': job.title,
                    'company': job.company,
                    'location': job.location or job.city,
                    'salary_min': float(job.salary_min) if job.salary_min else None,
                    'salary_max': float(job.salary_max) if job.salary_max else None,
                    'salary_currency': job.salary_currency,
                    'url': job.url,
                    'published_date': job.published_date.isoformat() if job.published_date else None
                }
                for job in jobs
            ],
            'total': total,
            'page': page,
            'pages': (total + per_page - 1) // per_page
        })
    finally:
        try:
            next(db_gen, None)
        except StopIteration:
            pass

# bot/webapp/templates/index.html
"""
<!DOCTYPE html>
<html>
<head>
    <title>WorkSearchBot</title>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <script src="https://telegram.org/js/telegram-web-app.js"></script>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto;
            margin: 0;
            padding: 20px;
            background: var(--tg-theme-bg-color);
            color: var(--tg-theme-text-color);
        }
        .search-box {
            width: 100%;
            padding: 12px;
            margin-bottom: 20px;
            border: 1px solid var(--tg-theme-hint-color);
            border-radius: 8px;
            font-size: 16px;
        }
        .job-card {
            background: var(--tg-theme-secondary-bg-color);
            padding: 15px;
            margin-bottom: 15px;
            border-radius: 10px;
        }
        .job-title {
            font-size: 18px;
            font-weight: bold;
            margin-bottom: 5px;
        }
        .job-company {
            color: var(--tg-theme-hint-color);
            margin-bottom: 5px;
        }
        .job-location {
            margin-bottom: 5px;
        }
        .job-salary {
            color: var(--tg-theme-link-color);
            font-weight: bold;
        }
    </style>
</head>
<body>
    <input type="text" id="searchBox" class="search-box" placeholder="Пошук вакансій...">
    <div id="results"></div>
    
    <script>
        let tg = window.Telegram.WebApp;
        tg.expand();
        
        const searchBox = document.getElementById('searchBox');
        const resultsDiv = document.getElementById('results');
        
        let searchTimeout;
        searchBox.addEventListener('input', () => {
            clearTimeout(searchTimeout);
            searchTimeout = setTimeout(search, 500);
        });
        
        async function search() {
            const query = searchBox.value;
            const response = await fetch(`/api/search?q=${encodeURIComponent(query)}`);
            const data = await response.json();
            
            resultsDiv.innerHTML = '';
            data.jobs.forEach(job => {
                const card = document.createElement('div');
                card.className = 'job-card';
                card.innerHTML = `
                    <div class="job-title">${job.title}</div>
                    <div class="job-company">${job.company || 'Компанія не вказана'}</div>
                    <div class="job-location">📍 ${job.location || 'Локація не вказана'}</div>
                    ${job.salary_min ? `<div class="job-salary">💰 від ${job.salary_min} ${job.salary_currency}</div>` : ''}
                `;
                card.onclick = () => tg.openLink(job.url);
                resultsDiv.appendChild(card);
            });
        }
        
        search();
    </script>
</body>
</html>
"""

# Додайте кнопку Web App в keyboards:
# bot/keyboards/main_menu.py
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo

def get_main_menu_keyboard():
    keyboard = [
        [
            InlineKeyboardButton("🔍 Пошук", callback_data="search"),
            InlineKeyboardButton("📊 Статистика", callback_data="stats")
        ],
        [
            InlineKeyboardButton("⭐ Обрані", callback_data="favorites"),
            InlineKeyboardButton("🔔 Підписки", callback_data="subscriptions")
        ],
        [
            InlineKeyboardButton("⚙️ Фільтри", callback_data="filters"),
            InlineKeyboardButton("💡 Рекомендації", callback_data="recommendations")
        ],
        [
            InlineKeyboardButton(
                "🌐 Web App",
                web_app=WebAppInfo(url="https://your-webapp-url.com")
            )
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

# Додайте в requirements.txt:
# flask==3.0.0
```

---

## 📋 ПІДСУМОК

### Пріоритети виправлень:

**🔴 Критичні (виправити негайно):**
1. SQL Injection через ILIKE запити
2. Відкритий доступ до секретних токенів
3. N+1 Query Problem

**🟡 Високі (виправити найближчим часом):**
1. Відсутність валідації користувацького вводу
2. Відсутність індексів на часто використовуваних полях
3. Синхронний скрапінг блокує event loop

**🟢 Середні (можна відкласти):**
1. Відсутність rate limiting
2. Потенційна DoS через необмежений запит до БД
3. Логування чутливої інформації
4. Відсутність кешування
5. Неоптимізоване завантаження результатів
6. Витік пам'яті через user_search_state

### Рекомендовані нові фічі (за пріоритетом):

1. **Автоматичні сповіщення про нові вакансії** - найбільш корисна фіча для користувачів
2. **Аналітика та рекомендації** - покращує UX та retention
3. **Експорт у PDF/Excel** - додає цінності для професійного використання
4. **Розширений пошук з AI** - диференціює від конкурентів
5. **Telegram Web App** - сучасний UX для складних взаємодій

---

**Автор:** Автоматичний аналіз коду WorkSearchBot  
**Дата:** 2026-02-01
