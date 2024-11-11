from sqlalchemy import JSON, Column, DateTime, Integer, String
from sqlalchemy.sql import func

from app.config.database import Base


class ReceiptApproverResponse(Base):
    __tablename__ = "receipt_approver_responses"
    receipt_id = Column(Integer, primary_key=True, nullable=False)
    client = Column(String, nullable=False)
    ocr_raw = Column(JSON, nullable=False)
    processed = Column(JSON, nullable=False)
    user_input_data = Column(JSON, nullable=False)
    receipt_classifier_response = Column(JSON, nullable=True)
    last_updated = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    def __str__(self):
        return f"<ReceiptApproverResponse id={self.receipt_id}, client={self.client}, last_updated={self.last_updated}>"
