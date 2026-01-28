from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, DECIMAL, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

Base = declarative_base()


class User(Base):
    """Модель користувача"""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    telegram_id = Column(Integer, unique=True, index=True, nullable=False)
    username = Column(String(255), nullable=True)
    first_name = Column(String(255), nullable=True)
    language_code = Column(String(10), default="uk")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active = Column(Boolean, default=True)
    
    # Зв'язки
    subscriptions = relationship("UserSubscription", back_populates="user", cascade="all, delete-orphan")
    favorites = relationship("UserFavorite", back_populates="user", cascade="all, delete-orphan")
    search_history = relationship("SearchHistory", back_populates="user", cascade="all, delete-orphan")


class JobListing(Base):
    """Модель оголошення про роботу"""
    __tablename__ = "job_listings"
    
    id = Column(Integer, primary_key=True, index=True)
    source = Column(String(50), nullable=False, index=True)  # olx, pracuj.pl, indeed, etc.
    source_id = Column(String(255), nullable=True)  # ID на оригінальному сайті
    title = Column(String(500), nullable=False)
    description = Column(Text, nullable=True)
    company = Column(String(255), nullable=True)
    location = Column(String(255), nullable=True)
    city = Column(String(100), nullable=True, index=True)
    salary_min = Column(DECIMAL(10, 2), nullable=True)
    salary_max = Column(DECIMAL(10, 2), nullable=True)
    salary_currency = Column(String(10), default="PLN")
    employment_type = Column(String(50), nullable=True)  # full-time, part-time, contract
    category = Column(String(100), nullable=True, index=True)
    url = Column(String(1000), unique=True, nullable=False)
    published_date = Column(DateTime, nullable=True)
    scraped_at = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Boolean, default=True, index=True)
    
    # Зв'язки
    favorites = relationship("UserFavorite", back_populates="job_listing", cascade="all, delete-orphan")


class UserSubscription(Base):
    """Модель підписки користувача"""
    __tablename__ = "user_subscriptions"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    city = Column(String(100), nullable=True)
    category = Column(String(100), nullable=True)
    salary_min = Column(DECIMAL(10, 2), nullable=True)
    keywords = Column(Text, nullable=True)  # JSON масив ключових слів
    notification_frequency = Column(String(20), default="instant")  # instant, daily, weekly
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Зв'язки
    user = relationship("User", back_populates="subscriptions")


class UserFavorite(Base):
    """Модель улюбленої вакансії"""
    __tablename__ = "user_favorites"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    job_listing_id = Column(Integer, ForeignKey("job_listings.id"), nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Зв'язки
    user = relationship("User", back_populates="favorites")
    job_listing = relationship("JobListing", back_populates="favorites")


class SearchHistory(Base):
    """Модель історії пошуку"""
    __tablename__ = "search_history"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    query = Column(String(500), nullable=True)
    filters = Column(JSON, nullable=True)
    results_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    
    # Зв'язки
    user = relationship("User", back_populates="search_history")
