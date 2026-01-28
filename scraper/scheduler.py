"""Планувальник задач для скрапінгу"""
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from datetime import datetime
import logging
from config import settings
from database.database import get_db
from database.models import JobListing
from scraper.scrapers.olx_scraper import OLXScraper
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


class ScrapingScheduler:
    """Планувальник для автоматичного скрапінгу"""
    
    def __init__(self):
        self.scheduler = AsyncIOScheduler()
        self.scrapers = [
            OLXScraper(),
            # Тут можна додати інші скрапери
        ]
    
    def start(self):
        """Запускає планувальник"""
        if not settings.SCRAPING_ENABLED:
            logger.info("Скрапінг вимкнено в налаштуваннях")
            return
        
        # Додаємо задачу на періодичний скрапінг
        self.scheduler.add_job(
            self.scrape_all,
            trigger=IntervalTrigger(minutes=settings.SCRAPING_INTERVAL_MINUTES),
            id='scrape_jobs',
            name='Scrape job listings',
            replace_existing=True
        )
        
        self.scheduler.start()
        logger.info(f"Планувальник скрапінгу запущено. Інтервал: {settings.SCRAPING_INTERVAL_MINUTES} хвилин")
    
    def stop(self):
        """Зупиняє планувальник"""
        self.scheduler.shutdown()
        logger.info("Планувальник скрапінгу зупинено")
    
    async def scrape_all(self):
        """Запускає скрапінг для всіх джерел"""
        logger.info("Початок скрапінгу вакансій...")
        
        for scraper in self.scrapers:
            try:
                await self.scrape_source(scraper)
            except Exception as e:
                logger.error(f"Помилка при скрапінгу {scraper.source_name}: {e}")
        
        logger.info("Скрапінг завершено")
    
    async def scrape_source(self, scraper):
        """Скрапить одне джерело"""
        logger.info(f"Скрапінг {scraper.source_name}...")
        
        # Отримуємо вакансії
        jobs = scraper.fetch_jobs(max_pages=3)  # Обмежуємо кількість сторінок
        
        db_gen = get_db()
        db: Session = next(db_gen)
        new_jobs_count = 0
        updated_jobs_count = 0
        
        try:
            for job_data in jobs:
                try:
                    # Парсимо деталі
                    normalized_job = scraper.parse_job(job_data)
                    
                    if not normalized_job.get('url'):
                        continue
                    
                    # Перевіряємо чи вже є така вакансія
                    existing_job = db.query(JobListing).filter(
                        JobListing.url == normalized_job['url']
                    ).first()
                    
                    if existing_job:
                        # Оновлюємо існуючу
                        for key, value in normalized_job.items():
                            if hasattr(existing_job, key) and value:
                                setattr(existing_job, key, value)
                        existing_job.scraped_at = datetime.utcnow()
                        updated_jobs_count += 1
                    else:
                        # Створюємо нову
                        new_job = JobListing(**normalized_job)
                        db.add(new_job)
                        new_jobs_count += 1
                    
                except Exception as e:
                    logger.error(f"Помилка при збереженні вакансії: {e}")
                    continue
            
            db.commit()
            logger.info(
                f"{scraper.source_name}: додано {new_jobs_count} нових, "
                f"оновлено {updated_jobs_count} вакансій"
            )
        finally:
            # Закриваємо сесію
            try:
                next(db_gen, None)
            except StopIteration:
                pass
