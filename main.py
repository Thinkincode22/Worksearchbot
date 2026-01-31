"""Головний файл запуску бота"""
import asyncio
import logging
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
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
import http.server
import socketserver
import threading
import os

# Налаштування логування
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

class HealthHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/plain')
        self.end_headers()
        self.wfile.write(b"OK")
    
    def log_message(self, format, *args):
        return # Вимикаємо логи для health check

def run_health_server():
    """Запускає простий HTTP-сервер для health check на Render"""
    port = int(os.environ.get("PORT", 8000))
    try:
        httpd = http.server.HTTPServer(("0.0.0.0", port), HealthHandler)
        logger.info(f"Health check server started on port {port}")
        httpd.serve_forever()
    except Exception as e:
        logger.error(f"Failed to start health check server: {e}")

# Вимикаємо стандартні логи loguru до налаштування у main
logger.remove()

LOG_FORMAT = (
    "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
    "<level>{level: <8}</level> | "
    "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>"
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
    
    # Callback queries (кнопки) - спочатку специфічні паттерни
    application.add_handler(CallbackQueryHandler(page_callback_handler, pattern="^page_"))
    application.add_handler(CallbackQueryHandler(start_handler, pattern="^main_menu$"))
    application.add_handler(CallbackQueryHandler(search_handler, pattern="^search$"))
    application.add_handler(CallbackQueryHandler(stats_handler, pattern="^stats$"))
    
    # Фільтри
    application.add_handler(CallbackQueryHandler(filters_handler, pattern="^filters$"))
    application.add_handler(CallbackQueryHandler(filter_callback_handler, pattern="^(filter_|city_|category_|employment_)"))
    
    # Улюблені
    application.add_handler(CallbackQueryHandler(favorites_handler, pattern="^favorites$"))
    application.add_handler(CallbackQueryHandler(favorite_callback_handler, pattern="^favorite_"))
    
    # Підписки
    application.add_handler(CallbackQueryHandler(subscriptions_handler, pattern="^subscriptions$"))
    application.add_handler(CallbackQueryHandler(subscription_callback_handler, pattern="^subscription_"))
    
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
    # 1. Початкове логування у консоль
    logging.info("Початок запуску бота...")

    # 2. Відкриваємо порт для Render (Health Check) якнайшвидше (тільки для Polling)
    if not settings.USE_WEBHOOKS:
        threading.Thread(target=run_health_server, daemon=True).start()
    else:
        logger.info("Webhook mode enabled: health check server will be handled by webhook port")

    # 3. Створюємо папки та налаштовуємо логування
    os.makedirs("logs", exist_ok=True)
    
    # Налаштування логування у файл та консоль
    logger.add(
        settings.LOG_FILE,
        rotation="10 MB",
        retention="7 days",
        level=settings.LOG_LEVEL,
        format=LOG_FORMAT
    )
    
    # Додаємо кольоровий вивід у консоль
    import sys
    logger.add(sys.stderr, format=LOG_FORMAT, level=settings.LOG_LEVEL)
    
    logger.info("="*50)
    logger.info("🚀 ЗАПУСК НОВОЇ СЕСІЇ БОТА")
    logger.info("="*50)

    # 4. Перевіряємо токен
    if not settings.TELEGRAM_BOT_TOKEN:
        logger.error("TELEGRAM_BOT_TOKEN не встановлено! Бот не може запуститись.")
        return
    
    # 5. Ініціалізуємо БД
    try:
        logger.info("Ініціалізація бази даних...")
        init_db()
    except Exception as e:
        logger.error(f"Критична помилка при ініціалізації БД: {e}")
        # Не зупиняємось, можливо БД підніметься пізніше
    
    # 6. Створюємо додаток
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
    if settings.USE_WEBHOOKS:
        if not settings.WEBHOOK_URL:
            logger.error("WEBHOOK_URL не встановлено! Використовуйте Polling або вкажіть URL.")
            return
            
        logger.info(f"Запуск у режимі Webhook: {settings.WEBHOOK_URL}")
        port = int(os.environ.get("PORT", 8000))
        
        application.run_webhook(
            listen="0.0.0.0",
            port=port,
            url_path=settings.WEBHOOK_SECRET_TOKEN,
            webhook_url=f"{settings.WEBHOOK_URL}/{settings.WEBHOOK_SECRET_TOKEN}",
            allowed_updates=Update.ALL_TYPES,
            drop_pending_updates=True
        )
    else:
        logger.info("Запуск у режимі Polling...")
        while True:
            try:
                application.run_polling(
                    allowed_updates=Update.ALL_TYPES,
                    drop_pending_updates=True,
                    close_loop=False # Важливо для рестарту
                )
            except Exception as e:
                logger.error(f"⚠️ Критична помилка у циклі polling: {e}")
                logger.info("Спроба перезапуску через 5 секунд...")
                import time
                time.sleep(5)
            else:
                break


if __name__ == "__main__":
    main()
