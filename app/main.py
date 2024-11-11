from fastapi import FastAPI
from fastapi.concurrency import asynccontextmanager

from app.api import endpoints
from app.config.database import Base, engine
from app.config.logging_config import setup_logging

from .receipt_approver.views import router as receipt_approver_router

# Setup logging
logger = setup_logging()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup event
    logger.info("Starting application...")
    Base.metadata.create_all(bind=engine)
    logger.info(f"Tables created: {Base.metadata.tables.keys()}")

    yield

    # Shutdown event
    logger.info("Shutting down application...")


app = FastAPI()


app.include_router(endpoints.router)
app.include_router(receipt_approver_router, prefix="/receipts", tags=["receipts"])
