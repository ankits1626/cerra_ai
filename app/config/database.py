from sqlalchemy import create_engine
from sqlalchemy.exc import SQLAlchemyError

# from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import declarative_base, sessionmaker

from app.config.logging_config import setup_logging
from app.config.settings import settings

# Setup logging
logger = setup_logging()
# Using the DATABASE_URL from settings
engine = create_engine(settings.DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    except SQLAlchemyError as e:
        logger.error(f"Database error: {e}")
        raise
    finally:
        db.close()
