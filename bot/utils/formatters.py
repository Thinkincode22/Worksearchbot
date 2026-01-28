"""Форматування повідомлень для бота"""
from datetime import datetime
from database.models import JobListing
from config.constants import EMOJIS


def format_job_listing(job: JobListing) -> str:
    """Форматує оголошення про роботу для відображення"""
    text = f"{EMOJIS['company']} <b>{job.title}</b>\n\n"
    
    if job.company:
        text += f"{EMOJIS['company']} Компанія: {job.company}\n"
    
    if job.city or job.location:
        location = job.city or job.location
        text += f"{EMOJIS['location']} Місто: {location}\n"
    
    if job.salary_min or job.salary_max:
        salary_text = ""
        if job.salary_min and job.salary_max:
            salary_text = f"{job.salary_min:.0f} - {job.salary_max:.0f}"
        elif job.salary_min:
            salary_text = f"від {job.salary_min:.0f}"
        elif job.salary_max:
            salary_text = f"до {job.salary_max:.0f}"
        
        if salary_text:
            text += f"{EMOJIS['salary']} Зарплата: {salary_text} {job.salary_currency}\n"
    
    if job.employment_type:
        from config.constants import EMPLOYMENT_TYPES
        emp_type = EMPLOYMENT_TYPES.get(job.employment_type, job.employment_type)
        text += f"{EMOJIS['time']} Тип: {emp_type}\n"
    
    if job.published_date:
        days_ago = (datetime.utcnow() - job.published_date).days
        if days_ago == 0:
            date_text = "сьогодні"
        elif days_ago == 1:
            date_text = "вчора"
        else:
            date_text = f"{days_ago} днів тому"
        text += f"{EMOJIS['date']} Опубліковано: {date_text}\n"
    
    if job.description:
        # Обрізаємо опис до 300 символів
        description = job.description[:300]
        if len(job.description) > 300:
            description += "..."
        text += f"\n{EMOJIS['description']} Опис:\n{description}\n"
    
    text += f"\n{EMOJIS['link']} <a href='{job.url}'>Детальніше</a>"
    
    return text


def format_subscription_info(subscription) -> str:
    """Форматує інформацію про підписку"""
    from config.constants import NOTIFICATION_FREQUENCIES
    
    text = f"{EMOJIS['subscriptions']} <b>Підписка #{subscription.id}</b>\n\n"
    
    filters = []
    if subscription.city:
        filters.append(f"Місто: {subscription.city}")
    if subscription.category:
        filters.append(f"Категорія: {subscription.category}")
    if subscription.salary_min:
        filters.append(f"Зарплата від: {subscription.salary_min} PLN")
    if subscription.keywords:
        import json
        try:
            keywords = json.loads(subscription.keywords)
            if keywords:
                filters.append(f"Ключові слова: {', '.join(keywords)}")
        except:
            pass
    
    if filters:
        text += "Фільтри:\n" + "\n".join(f"• {f}" for f in filters) + "\n\n"
    
    freq = NOTIFICATION_FREQUENCIES.get(subscription.notification_frequency, subscription.notification_frequency)
    text += f"Частота сповіщень: {freq}\n"
    text += f"Статус: {'Активна' if subscription.is_active else 'Неактивна'}"
    
    return text


def format_stats(stats: dict) -> str:
    """Форматує статистику"""
    text = f"{EMOJIS['stats']} <b>Статистика</b>\n\n"
    
    if 'total_jobs' in stats:
        text += f"Всього вакансій: {stats['total_jobs']}\n"
    if 'total_users' in stats:
        text += f"Всього користувачів: {stats['total_users']}\n"
    if 'jobs_by_city' in stats:
        text += "\nВакансії по містах:\n"
        for city, count in list(stats['jobs_by_city'].items())[:10]:
            text += f"• {city}: {count}\n"
    
    return text
