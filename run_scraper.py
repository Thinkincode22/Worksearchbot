import asyncio
import logging
from scraper.scheduler import ScrapingScheduler

# Налаштування логування
logging.basicConfig(level=logging.INFO)

async def main():
    print("Запуск ручного скрапінгу...")
    scheduler = ScrapingScheduler()
    await scheduler.scrape_all()
    print("Скрапінг завершено!")

if __name__ == "__main__":
    asyncio.run(main())
