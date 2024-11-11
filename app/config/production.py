import os

from .settings import Settings


class ProductionSettings(Settings):
    DEBUG: bool = False
    DB_NAME: str = os.getenv("DEV_DB_NAME", "dev_database")
    # Add other production-specific settings here


settings = ProductionSettings()
