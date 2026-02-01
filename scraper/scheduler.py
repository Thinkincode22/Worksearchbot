"""Планувальник задач для скрапінгу"""
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from datetime import datetime
import logging
from config import settings
from database.database import get_db
from database.models import JobListing
from scraper.scrapers.olx_scraper import OLXScraper
from scraper.scrapers.pracuj_scraper import PracujScraper
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


class ScrapingScheduler:
    """Планувальник для автоматичного скрапінгу"""
    
    def __init__(self):
        self.scheduler = AsyncIOScheduler()
        self.scrapers = [
            OLXScraper(),
            PracujScraper(),
        ]
    
    def start(self):
        """Запускає планувальник"""
        if not settings.SCRAPING_ENABLED:
            logger.info("Скрапінг вимкнено в налаштуваннях")
            return
        
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
        
        import asyncio
        # Отримуємо вакансії у окремому потоці, щоб не блокувати event loop
        jobs = await asyncio.to_thread(scraper.fetch_jobs, max_pages=3)
        
        db_gen = get_db()
        db: Session = next(db_gen)
        new_jobs_count = 0
        updated_jobs_count = 0
        seen_urls = set()  # Уникальність в межах одного батчу
        
        try:
            for job_data in jobs:
                try:
                    # Парсимо деталі у окремому потоці
                    normalized_job = await asyncio.to_thread(scraper.parse_job, job_data)
                    
                    url = normalized_job.get('url')
                    if not url or url in seen_urls:
                        continue
                    
                    seen_urls.add(url)
                    
                    # Перевіряємо чи вже є така вакансія в БД
                    existing_job = db.query(JobListing).filter(
                        JobListing.url == url
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
