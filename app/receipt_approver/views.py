import base64
import logging
from typing import Dict, Optional

import boto3
from botocore.exceptions import BotoCoreError, ClientError
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import inspect
from sqlalchemy.orm import Session

from app.config.database import get_db
from app.config.settings import settings
from app.receipt_approver.crud import save_receipt_approver_response
from app.receipt_approver.model_utils import predict_receipt_type
from app.receipt_approver.models import ReceiptApproverResponse

from .schemas import (
    FetchReceiptValidationDataRequest,
    ReceiptApproverResponseSchema,
    ReceiptData,
)
from .validator_factory import ValidatorFactory

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/receipt-validation-data", response_model=ReceiptApproverResponseSchema)
def get_receipt_validation_data(
    request: Request,
    data: FetchReceiptValidationDataRequest,
    db: Session = Depends(get_db),
):
    """
    Fetch validation data of a receipt based on its receipt id
    ### Input:
    - FetchReceiptValidationDataRequest model encapsulating the receipt_id
    ### Output:
    - **ReceiptApproverResponseSchema**: Contains the validation result, OCR data,
        and prediction information.
    - Returns an HTTPException with error details if receipt not found.
    """
    # Example filtering based on criteria in ReceiptValidationRequest
    receipt = (
        db.query(ReceiptApproverResponse)
        .filter(ReceiptApproverResponse.receipt_id == data.receipt_id)
        .first()
    )

    # Check if the receipt was found
    if receipt is None:
        raise HTTPException(status_code=404, detail="Receipt not found")

    # Convert SQLAlchemy model to Pydantic schema
    response_data = ReceiptApproverResponseSchema.from_orm_with_custom_fields(receipt)

    return response_data


@router.post("/validate-receipt", response_model=ReceiptApproverResponseSchema)
def validate_receipt(
    request: Request, data: ReceiptData, db: Session = Depends(get_db)
):
    """
    Validates a receipt by processing its OCR data, making a receipt type prediction,
    and applying custom validation rules.

    ### Input:
    - ReceiptData model containing the receipt information such as:
      - **receipt_id**: The unique identifier of the receipt.
      - **receipt_number**: receipt number entered by user.
      - **receipt_date**: The date the receipt was issued.
      - **receipt_client**: The client for which the receipt validation is being processed.
      - **encoded_receipt_file**: Base64-encoded string of the receipt image.

    ### Output:
    - **ReceiptApproverResponseSchema**: Contains the validation result, OCR data,
        and prediction information.
    - Returns an HTTPException with error details if validation or processing fails.
    """
    existing_response = retrieve_existing_response(db, data.receipt_id)
    keras_label, keras_prediction = make_keras_prediction(data.encoded_receipt_file)

    file_data = get_decoded_data(data.encoded_receipt_file)

    ocr_raw = (
        existing_response.ocr_raw if existing_response else analyze_document(file_data)
    )

    validator = get_validator(data.receipt_client, data.model_dump(), ocr_raw)
    validator_response = validator.validate()
    retval = save_response_and_return_result(
        db, ocr_raw, validator_response, keras_label, keras_prediction, data
    )
    return ReceiptApproverResponseSchema.from_orm_with_custom_fields(retval)


def get_decoded_data(encoded_data):
    try:
        return base64.b64decode(encoded_data)
    except Exception:
        raise HTTPException(status_code=400, detail="Encoded image is Invalid.")


def retrieve_existing_response(
    db: Session, receipt_id: int
) -> Optional[ReceiptApproverResponse]:
    try:
        retval = (
            db.query(ReceiptApproverResponse)
            .filter(ReceiptApproverResponse.receipt_id == receipt_id)
            .first()
        )
        return retval
    except Exception as e:
        logger.info(
            f"Failed to retrieve existing result for receipt_ID = {receipt_id}: {e}"
        )
        return None


def make_keras_prediction(encoded_receipt_file: str):
    try:
        # Get the label and prediction in a single call
        keras_label, keras_prediction = predict_receipt_type(encoded_receipt_file)
        logger.info(
            f"Keras prediction: Label={keras_label}, Confidence={keras_prediction}"
        )
        return keras_label, keras_prediction
    except HTTPException as e:
        # Re-raise the HTTP exception with more context if needed
        logger.error(f"Prediction HTTPException: {e.detail}")
        return None, None
    except Exception as e:
        # General catch-all for unexpected errors
        logger.error(f"Unexpected error during Keras model prediction: {str(e)}")
        return None, None


def get_validator(receipt_client: str, user_input: Dict, response: Dict):
    try:
        return ValidatorFactory.get_validator(receipt_client, user_input, response)
    except ValueError as e:
        logger.error(f"Validator not found for client: {receipt_client}, error: {e}")
        raise HTTPException(status_code=400, detail=str(e))


# @retry(wait=wait_fixed(2), stop=stop_after_attempt(3))
def analyze_document(file_data: bytes) -> dict:
    boto_client = boto3.client(
        "textract",
        region_name=settings.OCR_AWS_REGION_NAME,
        aws_access_key_id=settings.OCR_AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.OCR_AWS_SECRET_ACCESS_KEY,
    )
    try:
        return boto_client.analyze_document(
            Document={"Bytes": file_data},
            FeatureTypes=["TABLES", "FORMS", "QUERIES"],
            QueriesConfig={
                "Queries": [
                    {"Alias": "Date", "Text": "Date"},
                    {"Alias": "Order Date", "Text": "Order Date"},
                ]
            },
        )
    except (BotoCoreError, ClientError) as e:
        logger.error(f"Error in Textract analysis: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Textract error: {str(e)}")


def save_response_and_return_result(
    db: Session,
    ocr_raw: dict,
    validator_response: dict,
    keras_label: str,
    keras_prediction: float,
    data: ReceiptData,
) -> ReceiptApproverResponse:
    bind_engine = db.get_bind()
    logger.info(
        f"<<<<<<<< Engine URL: {bind_engine.url} Is Engine In-Memory: \
        {'sqlite' in bind_engine.url.drivername and ':memory:' in str(bind_engine.url)}"
    )
    # Use SQLAlchemy inspector to get the list of tables
    inspector = inspect(bind_engine)
    tables = inspector.get_table_names()
    logger.info(f"List of Tables: {tables}")
    try:
        keras_prediction_data = (
            {}
            if keras_label is None or keras_prediction is None
            else {
                "label": keras_label,
                "confidence": float(keras_prediction),
            }
        )

        response = save_receipt_approver_response(
            db,
            ocr_raw,
            validator_response,
            data.receipt_client,
            data,
            keras_prediction_data,
        )

        return response
    except Exception as e:
        logger.error(f"Unable save response: {str(e)}")
        raise HTTPException(status_code=500, detail=f"{str(e)}")
