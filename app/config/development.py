import os

from .settings import Settings


class DevelopmentSettings(Settings):
    DEBUG: bool = True
    DB_NAME: str = os.getenv("DEV_DB_NAME", "ai_dev_db")


dev_settings = DevelopmentSettings()
