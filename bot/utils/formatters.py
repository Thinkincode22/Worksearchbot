"""Форматування повідомлень для бота"""
from datetime import datetime
from database.models import JobListing
from config.constants import EMOJIS


def format_job_listing(job: JobListing, include_url: bool = True) -> str:
    """Форматує оголошення про роботу для відображення"""
    # Заголовок вакансії як посилання (якщо є URL)
    if include_url and job.url:
        text = f'🔎 <a href="{job.url}"><b>{job.title}</b></a>\n\n'
    else:
        text = f"🔎 <b>{job.title}</b>\n\n"
    
    # Місто з іконкою
    if job.city or job.location:
        location = job.city or job.location
        text += f"📍 Місто: {location}\n\n"
    
    # Опис з іконкою
    if job.description:
        # Обрізаємо опис до 400 символів для кращої читабельності
        description = job.description[:400].strip()
        if len(job.description) > 400:
            description += "..."
        text += f"📝 Опис:\n{description}\n"
    
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
