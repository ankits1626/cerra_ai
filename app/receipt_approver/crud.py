import logging

from sqlalchemy.orm import Session

from .models import ReceiptApproverResponse
from .schemas import ReceiptData

logger = logging.getLogger(__name__)


def get_existing_response(db: Session, receipt_id: int) -> ReceiptApproverResponse:
    """
    Fetch the existing ReceiptApproverResponse from the database based on receipt_id.
    """
    try:
        return (
            db.query(ReceiptApproverResponse)
            .filter(ReceiptApproverResponse.receipt_id == receipt_id)
            .first()
        )
    except Exception:
        logger.error(
            f"Failed to retrieve existing response for receipt {receipt_id}",
            exc_info=True,
        )
        return None


def create_user_input_data(receipt_data: ReceiptData) -> dict:
    """
    Create a dictionary for the user input data from receipt_data.
    """
    return {
        "receipt_id": receipt_data.receipt_id,
        "receipt_number": receipt_data.receipt_number,
        "receipt_date": receipt_data.receipt_date,
        "brand": receipt_data.brand,
        "brand_model": receipt_data.brand_model,
    }


def update_existing_response(
    response: ReceiptApproverResponse,
    ocr_raw: dict,
    processed: dict,
    client: str,
    user_input_data: dict,
    receipt_classifier_response: dict,
) -> None:
    """
    Update fields in the existing ReceiptApproverResponse object.
    """
    response.ocr_raw = ocr_raw
    response.processed = processed
    response.client = client
    response.user_input_data = user_input_data
    response.receipt_classifier_response = receipt_classifier_response


def save_new_response(
    db: Session,
    receipt_id: int,
    ocr_raw: dict,
    processed: dict,
    client: str,
    user_input_data: dict,
    receipt_classifier_response: dict,
) -> ReceiptApproverResponse:
    """
    Create a new ReceiptApproverResponse and add it to the session.
    """
    response = ReceiptApproverResponse(
        receipt_id=receipt_id,
        ocr_raw=ocr_raw,
        processed=processed,
        client=client,
        user_input_data=user_input_data,
        receipt_classifier_response=receipt_classifier_response,
    )
    db.add(response)
    return response


def save_receipt_approver_response(
    db: Session,
    ocr_raw: dict,
    processed: dict,
    client: str,
    receipt_data: ReceiptData,
    receipt_classifier_response: dict,
) -> ReceiptApproverResponse:
    """
    Main function to either update an existing response or save a new one.
    """
    user_input_data = create_user_input_data(receipt_data)
    response = get_existing_response(db, receipt_data.receipt_id)

    try:
        if response:
            # Update the existing response
            update_existing_response(
                response,
                ocr_raw,
                processed,
                client,
                user_input_data,
                receipt_classifier_response,
            )
        else:
            # Create a new response
            response = save_new_response(
                db,
                receipt_data.receipt_id,
                ocr_raw,
                processed,
                client,
                user_input_data,
                receipt_classifier_response,
            )

        db.commit()
        db.refresh(response)
        return response

    except Exception as e:
        db.rollback()
        logger.error("Error while saving ReceiptApproverResponse", exc_info=True)
        raise e

    finally:
        db.close()
