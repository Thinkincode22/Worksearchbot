"""Валідація даних"""
import re
from typing import Optional


def validate_salary(salary_str: str) -> Optional[float]:
    """Валідує та парсить зарплату"""
    if not salary_str:
        return None
    
    # Видаляємо всі символи крім цифр та крапки
    cleaned = re.sub(r'[^\d.]', '', salary_str)
    
    try:
        salary = float(cleaned)
        if salary < 0 or salary > 1000000:  # Розумні межі
            return None
        return salary
    except ValueError:
        return None


def validate_city(city: str) -> bool:
    """Перевіряє чи місто в списку дозволених"""
    from config.constants import POLISH_CITIES
    return city in POLISH_CITIES


def validate_keywords(keywords_str: str) -> list:
    """Валідує та парсить ключові слова"""
    if not keywords_str:
        return []
    
    # Розділяємо по комах та очищаємо
    keywords = [kw.strip() for kw in keywords_str.split(",") if kw.strip()]
    
    # Обмежуємо кількість та довжину
    keywords = [kw[:50] for kw in keywords[:10]]
    
    return keywords


def sanitize_text(text: str, max_length: int = 1000) -> str:
    """Очищає текст від небезпечних символів"""
    if not text:
        return ""
    
    # Обрізаємо довжину
    text = text[:max_length]
    
    # Видаляємо потенційно небезпечні символи
    text = re.sub(r'[<>]', '', text)
    
    return text.strip()
