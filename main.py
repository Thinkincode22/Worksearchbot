"""Головний файл запуску бота"""
import asyncio
import logging
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters
)
from config import settings
from database.database import init_db
from bot.handlers import (
    start_handler,
    help_handler,
    search_handler,
    search_query_handler,
    filters_handler,
    filter_callback_handler,
    favorites_handler,
    favorite_callback_handler,
    subscriptions_handler,
    subscription_callback_handler,
    stats_handler
)
from bot.handlers.search import page_callback_handler
from scraper.scheduler import ScrapingScheduler
from loguru import logger

# Налаштування логування
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=getattr(logging, settings.LOG_LEVEL)
)

# Налаштування loguru
logger.add(
    settings.LOG_FILE,
    rotation="10 MB",
    retention="7 days",
    level=settings.LOG_LEVEL
)


def setup_handlers(application: Application):
    """Налаштовує обробники команд та повідомлень"""
    
    # Команди
    application.add_handler(CommandHandler("start", start_handler))
    application.add_handler(CommandHandler("help", help_handler))
    application.add_handler(CommandHandler("search", search_handler))
    application.add_handler(CommandHandler("filters", filters_handler))
    application.add_handler(CommandHandler("favorites", favorites_handler))
    application.add_handler(CommandHandler("subscriptions", subscriptions_handler))
    application.add_handler(CommandHandler("stats", stats_handler))
    
    # Callback queries (кнопки)
    application.add_handler(CallbackQueryHandler(start_handler, pattern="^main_menu$"))
    application.add_handler(CallbackQueryHandler(search_handler, pattern="^search$"))
    application.add_handler(CallbackQueryHandler(filters_handler, pattern="^filters$"))
    application.add_handler(CallbackQueryHandler(filter_callback_handler))
    application.add_handler(CallbackQueryHandler(favorites_handler, pattern="^favorites$"))
    application.add_handler(CallbackQueryHandler(favorite_callback_handler))
    application.add_handler(CallbackQueryHandler(subscriptions_handler, pattern="^subscriptions$"))
    application.add_handler(CallbackQueryHandler(subscription_callback_handler))
    application.add_handler(CallbackQueryHandler(stats_handler, pattern="^stats$"))
    application.add_handler(CallbackQueryHandler(page_callback_handler, pattern="^page_"))
    
    # Текстові повідомлення (пошук)
    application.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, search_query_handler)
    )


async def post_init(application: Application):
    """Виконується після ініціалізації бота"""
    logger.info("Бот ініціалізовано")
    
    # Запускаємо планувальник скрапінгу
    if settings.SCRAPING_ENABLED:
        scheduler = ScrapingScheduler()
        scheduler.start()
        application.bot_data['scheduler'] = scheduler


async def post_shutdown(application: Application):
    """Виконується при зупинці бота"""
    logger.info("Зупинка бота...")
    
    # Зупиняємо планувальник
    if 'scheduler' in application.bot_data:
        application.bot_data['scheduler'].stop()


def main():
    """Головна функція"""
    # Перевіряємо токен
    if not settings.TELEGRAM_BOT_TOKEN:
        logger.error("TELEGRAM_BOT_TOKEN не встановлено! Перевірте файл .env")
        return
    
    # Ініціалізуємо БД
    logger.info("Ініціалізація бази даних...")
    init_db()
    
    # Створюємо додаток з post_init та post_shutdown
    application = (
        Application.builder()
        .token(settings.TELEGRAM_BOT_TOKEN)
        .post_init(post_init)
        .post_shutdown(post_shutdown)
        .build()
    )
    
    # Налаштовуємо обробники
    setup_handlers(application)
    
    # Запускаємо бота
    logger.info("Запуск бота...")
    application.run_polling(
        allowed_updates=Update.ALL_TYPES,
        drop_pending_updates=True
    )


if __name__ == "__main__":
    main()
