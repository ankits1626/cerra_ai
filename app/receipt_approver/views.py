import base64
import logging
from typing import Dict

import boto3
from botocore.exceptions import BotoCoreError, ClientError
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.config.database import get_db
from app.config.settings import settings
from app.receipt_approver.crud import save_receipt_approver_response
from app.receipt_approver.model_utils import predict_receipt_type

from .models import ReceiptApproverResponse
from .schemas import ReceiptData
from .validator_factory import ValidatorFactory

router = APIRouter()

logger = logging.getLogger(__name__)


@router.post("/validate-receipt")
def validate_receipt(
    request: Request, data: ReceiptData, db: Session = Depends(get_db)
) -> Dict:
    logger.info(f"<<<<<<<< updated receipt # = {data.receipt_number}", request)
    logger.info(f"<<<<<<<< receipt client= {data.receipt_client}", request)
    logger.info(f"<<<<<<<< receipt date= {data.receipt_date}", request)

    try:
        existing_response = None
        if data.response_id:
            existing_response = (
                db.query(ReceiptApproverResponse)
                .filter(ReceiptApproverResponse.id == data.response_id)
                .first()
            )
        # Decode the base64 encoded file and make a prediction
        keras_label, keras_prediction = predict_receipt_type(data.encoded_receipt_file)

        # Log the result of Keras prediction
        logger.info(
            f"<<<<<<< Keras model predicted: {keras_label} with confidence {keras_prediction}"
        )

        # Decode the base64 encoded file
        file_data = base64.b64decode(data.encoded_receipt_file)
        receipt_date = data.receipt_date
        if existing_response:
            ocr_raw = existing_response.ocr_raw
        else:
            ocr_raw = analyze_document(file_data)

        # Get the appropriate validator
        try:
            validator = ValidatorFactory.get_validator(data.receipt_client)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))

        # Validate the Textract response
        validator_response = validator.validate(data.dict(), ocr_raw)
        response = save_receipt_approver_response(
            db,
            ocr_raw,
            validator_response,
            data.receipt_client,
            data,
            {
                "label": keras_label,
                "confidence": float(keras_prediction),
            },
        )

        response = {
            "id": str(response.id),
            "receipt_number": data.receipt_number,
            "receipt_date": data.receipt_date,
            "brand": data.brand,
            "receipt_type": response.receipt_classifier_response,
            "validation_result": validator_response,
            "last_updated": response.last_updated,
        }
        return response
    except Exception as e:
        print(f"<<<<< this error  = {e}")
        raise HTTPException(status_code=500, detail=str(e))


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
        logger.error(f"BotoCoreError in analyze_document: {str(e)}")
        raise e
