from bot.utils.db_helpers import get_db_session
from database.models import JobListing
from datetime import datetime

def add_mock_jobs():
    with get_db_session() as db:
        jobs = [
            JobListing(
                source="mock",
                source_id="1",
                title="Водій категорії B",
                description="Потрібен водій на бус, доставка по місту.",
                company="TransLogistics",
                location="Варшава",
                city="Warszawa",
                salary_min=5000,
                salary_max=7000,
                url="https://example.com/job1",
                published_date=datetime.now(),
                is_active=True
            ),
            JobListing(
                source="mock",
                source_id="2",
                title="Працівник складу",
                description="Пакування товарів, робота зі сканером.",
                company="Amazon",
                location="Вроцлав",
                city="Wrocław",
                salary_min=4500,
                salary_max=5500,
                url="https://example.com/job2",
                published_date=datetime.now(),
                is_active=True
            ),
            JobListing(
                source="mock",
                source_id="3",
                title="Будівельник",
                description="Внутрішні роботи, шпаклівка, фарбування.",
                company="BudMax",
                location="Краків",
                city="Kraków",
                salary_min=6000,
                salary_max=9000,
                url="https://example.com/job3",
                published_date=datetime.now(),
                is_active=True
            )
        ]
        
        for job in jobs:
            existing = db.query(JobListing).filter(JobListing.url == job.url).first()
            if not existing:
                db.add(job)
                print(f"Додано: {job.title}")
            else:
                print(f"Вже існує: {job.title}")
        
        db.commit()

if __name__ == "__main__":
    add_mock_jobs()
