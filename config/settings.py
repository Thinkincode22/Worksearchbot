from pydantic_settings import BaseSettings
from typing import List
import os
from dotenv import load_dotenv

load_dotenv()


class Settings(BaseSettings):
    """Налаштування проекту"""
    
    # Telegram Bot
    TELEGRAM_BOT_TOKEN: str = os.getenv("TELEGRAM_BOT_TOKEN", "")
    
    # Database
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL", 
        "sqlite:///./worksearchbot.db"
    )
    
    # Redis (опціонально)
    REDIS_URL: str = os.getenv("REDIS_URL", "")
    
    # Admin
    ADMIN_USER_IDS: str = os.getenv("ADMIN_USER_IDS", "")
    
    @property
    def admin_ids_list(self) -> List[int]:
        """Повертає список ID адмінів з валідацією"""
        if not self.ADMIN_USER_IDS:
            return []
        
        result = []
        for uid in self.ADMIN_USER_IDS.split(","):
            uid = uid.strip()
            if uid.isdigit():
                try:
                    user_id = int(uid)
                    # Валідація діапазону Telegram ID (позитивні числа до 2^63)
                    if 0 < user_id < 2**63:
                        result.append(user_id)
                except (ValueError, OverflowError):
                    # Ігноруємо невалідні ID
                    pass
        return result
    
    # Scraping
    SCRAPING_INTERVAL_MINUTES: int = int(os.getenv("SCRAPING_INTERVAL_MINUTES", "60"))
    SCRAPING_ENABLED: bool = os.getenv("SCRAPING_ENABLED", "true").lower() == "true"
    
    # Logging
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    LOG_FILE: str = os.getenv("LOG_FILE", "logs/bot.log")
    
    # Rate Limiting
    MAX_REQUESTS_PER_MINUTE: int = int(os.getenv("MAX_REQUESTS_PER_MINUTE", "30"))
    MAX_REQUESTS_PER_HOUR: int = int(os.getenv("MAX_REQUESTS_PER_HOUR", "200"))
    
    # Налаштування Webhook
    USE_WEBHOOKS: bool = os.getenv("USE_WEBHOOKS", "False").lower() == "true"
    WEBHOOK_URL: str = os.getenv("WEBHOOK_URL", "")
    
    @property
    def webhook_secret_token(self) -> str:
        """Повертає секретний токен для webhook з генерацією за замовчуванням"""
        import secrets
        token = os.getenv("WEBHOOK_SECRET_TOKEN")
        if not token:
            # Генеруємо випадковий токен якщо не вказано
            token = secrets.token_urlsafe(32)
        return token
    
    # Deprecated: використовуйте webhook_secret_token property замість цього
    WEBHOOK_SECRET_TOKEN: str = ""  # Буде ініціалізовано через property
    
    # User Agent для скраперів
    USER_AGENT: str = os.getenv(
        "USER_AGENT",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    )
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
