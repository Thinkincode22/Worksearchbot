from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
from config import settings
from .models import Base
import os

# Створюємо движок БД
db_url = settings.DATABASE_URL
if db_url.startswith("postgres://"):
    db_url = db_url.replace("postgres://", "postgresql://", 1)

if db_url.startswith("sqlite"):
    engine = create_engine(
        db_url,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
else:
    engine = create_engine(db_url)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Session:
    """Отримати сесію БД"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Ініціалізувати БД (створити таблиці)"""
    # Створюємо папку для логів якщо не існує
    os.makedirs("logs", exist_ok=True)
    
    # Визначаємо тип бази для логів (маскуємо пароль)
    safe_url = db_url.split('@')[-1] if '@' in db_url else db_url
    from loguru import logger
    logger.info(f"Ініціалізація бази даних: {safe_url}")
    
    try:
        # Створюємо всі таблиці
        Base.metadata.create_all(bind=engine)
        logger.info("База даних ініціалізована успішно!")
    except Exception as e:
        logger.error(f"Помилка ініціалізації бази даних: {e}")
        raise e
