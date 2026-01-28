from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
from config import settings
from .models import Base
import os

# Створюємо движок БД
if settings.DATABASE_URL.startswith("sqlite"):
    engine = create_engine(
        settings.DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
else:
    engine = create_engine(settings.DATABASE_URL)

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
    
    # Створюємо всі таблиці
    Base.metadata.create_all(bind=engine)
    print("База даних ініціалізована успішно!")
