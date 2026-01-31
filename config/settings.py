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
        """Повертає список ID адмінів"""
        if not self.ADMIN_USER_IDS:
            return []
        return [int(uid.strip()) for uid in self.ADMIN_USER_IDS.split(",") if uid.strip().isdigit()]
    
    # Scraping
    SCRAPING_INTERVAL_MINUTES: int = int(os.getenv("SCRAPING_INTERVAL_MINUTES", "60"))
    SCRAPING_ENABLED: bool = os.getenv("SCRAPING_ENABLED", "true").lower() == "true"
    
    # Logging
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    LOG_FILE: str = os.getenv("LOG_FILE", "logs/bot.log")
    
    # Rate Limiting
    MAX_REQUESTS_PER_MINUTE: int = int(os.getenv("MAX_REQUESTS_PER_MINUTE", "30"))
    MAX_REQUESTS_PER_HOUR: int = int(os.getenv("MAX_REQUESTS_PER_HOUR", "200"))
    
    # User Agent для скраперів
    USER_AGENT: str = os.getenv(
        "USER_AGENT",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    )
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
