from typing import Dict, Optional
from uuid import UUID

from pydantic import BaseModel


class ReceiptData(BaseModel):
    receipt_number: str
    receipt_date: str
    brand: str
    encoded_receipt_file: str
    receipt_client: str
    brand_model: str
    response_id: Optional[UUID] = None


class ReceiptApproverResponseCreate(BaseModel):
    ocr_raw: Dict
    processed: Dict
    client: str
    receipt_classifier_response: Dict
