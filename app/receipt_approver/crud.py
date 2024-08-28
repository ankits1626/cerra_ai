from fastapi import HTTPException
from sqlalchemy.orm import Session

from .models import ReceiptApproverResponse
from .schemas import ReceiptData


def save_receipt_approver_response(
    db: Session,
    ocr_raw: dict,
    processed: dict,
    client: str,
    receipt_data: ReceiptData,
    receipt_classifier_response: dict,
) -> ReceiptApproverResponse:
    if receipt_data.response_id:
        # Fetch the existing ReceiptApproverResponse from the database
        response = (
            db.query(ReceiptApproverResponse)
            .filter(ReceiptApproverResponse.id == receipt_data.response_id)
            .first()
        )

        if response:
            # Update the existing response
            response.ocr_raw = ocr_raw
            response.processed = processed
            response.client = client
            response.user_input_data = {
                "receipt_number": receipt_data.receipt_number,
                "receipt_date": receipt_data.receipt_date,
                "brand": receipt_data.brand,
                "brand_model": receipt_data.brand_model,
            }
            response.receipt_classifier_response = receipt_classifier_response
            db.commit()
            db.refresh(response)
            return response
        else:
            raise HTTPException(status_code=404, detail="Response ID not found.")
    else:
        # Create a new response
        response = ReceiptApproverResponse(
            ocr_raw=ocr_raw,
            processed=processed,
            client=client,
            user_input_data={
                "receipt_number": receipt_data.receipt_number,
                "receipt_date": receipt_data.receipt_date,
                "brand": receipt_data.brand,
                "brand_model": receipt_data.brand_model,
            },
            receipt_classifier_response=receipt_classifier_response,
        )
        db.add(response)
        db.commit()
        db.refresh(response)
        return response
