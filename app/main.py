from fastapi import FastAPI

from app.api import endpoints
from app.config.database import Base, engine

from .receipt_approver.views import router as receipt_approver_router

app = FastAPI()
app.include_router(endpoints.router)
app.include_router(receipt_approver_router, prefix="/receipts", tags=["receipts"])
# Create the database tables
Base.metadata.create_all(bind=engine)
