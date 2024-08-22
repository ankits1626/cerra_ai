from pydantic import BaseModel


class ReceiptData(BaseModel):
    receipt_number: str
    receipt_date: str
    brand: str
    encoded_receipt_file: str
    receipt_client: str
    brand_model: str
