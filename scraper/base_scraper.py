"""Базовий клас для скраперів"""
from abc import ABC, abstractmethod
from typing import List, Dict, Optional
from datetime import datetime
import requests
from bs4 import BeautifulSoup
from config import settings
import time
import logging

logger = logging.getLogger(__name__)


class BaseScraper(ABC):
    """Базовий клас для всіх скраперів"""
    
    def __init__(self, source_name: str, base_url: str):
        self.source_name = source_name
        self.base_url = base_url
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': settings.USER_AGENT,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'pl-PL,pl;q=0.9,en-US;q=0.8,en;q=0.7',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Cache-Control': 'max-age=0',
        })
    
    def fetch_page(self, url: str, retries: int = 3) -> Optional[str]:
        """Отримує HTML сторінку з retry логікою"""
        for attempt in range(retries):
            try:
                response = self.session.get(url, timeout=30)
                response.raise_for_status()
                
                # Додаємо випадкову затримку щоб не блокували (2-5 секунд)
                import random
                time.sleep(random.uniform(2, 5))
                
                return response.text
            except Exception as e:
                logger.warning(f"Помилка при отриманні {url} (спроба {attempt + 1}/{retries}): {e}")
                if attempt < retries - 1:
                    time.sleep(2 ** attempt)  # Exponential backoff
                else:
                    logger.error(f"Не вдалося отримати {url} після {retries} спроб")
        return None
    
    def parse_html(self, html: str) -> BeautifulSoup:
        """Парсить HTML"""
        return BeautifulSoup(html, 'lxml')
    
    @abstractmethod
    def fetch_jobs(self, max_pages: int = 5) -> List[Dict]:
        """
        Отримує список вакансій
        
        Args:
            max_pages: Максимальна кількість сторінок для парсингу
            
        Returns:
            Список словників з даними вакансій
        """
        pass
    
    @abstractmethod
    def parse_job(self, job_data: Dict) -> Dict:
        """
        Парсить окрему вакансію
        
        Args:
            job_data: Дані вакансії зі списку
            
        Returns:
            Словник з нормалізованими даними вакансії
        """
        pass
    
    def normalize_data(self, job_data: Dict) -> Dict:
        """
        Нормалізує дані вакансії
        
        Args:
            job_data: Дані вакансії
            
        Returns:
            Нормалізовані дані
        """
        normalized = {
            'source': self.source_name,
            'source_id': job_data.get('source_id'),
            'title': self._clean_text(job_data.get('title', '')),
            'description': self._clean_text(job_data.get('description', '')),
            'company': self._clean_text(job_data.get('company', '')),
            'location': self._clean_text(job_data.get('location', '')),
            'city': self._extract_city(job_data.get('location', '')),
            'salary_min': self._parse_salary(job_data.get('salary', ''), 'min'),
            'salary_max': self._parse_salary(job_data.get('salary', ''), 'max'),
            'salary_currency': job_data.get('salary_currency', 'PLN'),
            'employment_type': job_data.get('employment_type'),
            'category': job_data.get('category'),
            'url': job_data.get('url', ''),
            'published_date': self._parse_date(job_data.get('published_date', '')),
        }
        
        return normalized
    
    def _clean_text(self, text: str) -> str:
        """Очищає текст"""
        if not text:
            return ""
        # Видаляємо зайві пробіли та переноси
        text = ' '.join(text.split())
        return text.strip()
    
    def _extract_city(self, location: str) -> Optional[str]:
        """Витягує місто з локації"""
        if not location:
            return None
        
        from config.constants import POLISH_CITIES
        
        # Перевіряємо чи місто в списку
        for city in POLISH_CITIES:
            if city.lower() in location.lower():
                return city
        
        # Якщо не знайдено, повертаємо перше слово
        parts = location.split(',')
        if parts:
            return parts[0].strip()
        
        return None
    
    def _parse_salary(self, salary_str: str, mode: str = 'min') -> Optional[float]:
        """Парсить зарплату"""
        if not salary_str:
            return None
        
        import re
        # Шукаємо числа в тексті
        numbers = re.findall(r'\d+', salary_str.replace(' ', ''))
        
        if not numbers:
            return None
        
        try:
            if mode == 'min' and len(numbers) >= 1:
                return float(numbers[0])
            elif mode == 'max' and len(numbers) >= 2:
                return float(numbers[1])
            elif mode == 'max' and len(numbers) == 1:
                return float(numbers[0])
        except ValueError:
            pass
        
        return None
    
    def _parse_date(self, date_str: str) -> Optional[datetime]:
        """Парсить дату"""
        if not date_str:
            return None
        
        from dateutil import parser
        
        try:
            return parser.parse(date_str)
        except:
            # Спробуємо знайти дату в тексті
            import re
            date_patterns = [
                r'\d{4}-\d{2}-\d{2}',
                r'\d{2}\.\d{2}\.\d{4}',
                r'\d{2}/\d{2}/\d{4}',
            ]
            
            for pattern in date_patterns:
                match = re.search(pattern, date_str)
                if match:
                    try:
                        return parser.parse(match.group())
                    except:
                        continue
        
        return datetime.utcnow()
