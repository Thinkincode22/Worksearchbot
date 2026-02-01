"""Адмінські обробники для керування ботом"""
from telegram import Update
from telegram.ext import ContextTypes
import asyncio
import logging

logger = logging.getLogger(__name__)

async def update_jobs_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обробник команди /update_jobs"""
    # Можна додати перевірку на адміна тут
    # admin_id = settings.ADMIN_ID
    # if update.effective_user.id != admin_id:
    #     return
    
    await update.message.reply_text("🔄 Початок оновлення вакансій у фоновому режимі...")
    
    scheduler = context.application.bot_data.get('scheduler')
    if not scheduler:
        await update.message.reply_text("❌ Планувальник скрапінгу не знайдено.")
        return
    
    # Запускаємо скрапінг асинхронно
    asyncio.create_task(scheduler.scrape_all())
    
    await update.message.reply_text("✅ Запит на скрапінг прийнято. Слідкуйте за логами сервера.")
