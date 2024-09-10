import base64
import logging
from typing import Optional

import boto3
from botocore.exceptions import BotoCoreError, ClientError
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import inspect
from sqlalchemy.orm import Session
from tenacity import retry, stop_after_attempt, wait_fixed

from app.config.database import get_db
from app.config.settings import settings
from app.receipt_approver.crud import save_receipt_approver_response
from app.receipt_approver.model_utils import predict_receipt_type
from app.receipt_approver.models import ReceiptApproverResponse

from .schemas import ReceiptApproverResponseSchema, ReceiptData
from .validator_factory import ValidatorFactory

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/validate-receipt", response_model=ReceiptApproverResponseSchema)
def validate_receipt(
    request: Request, data: ReceiptData, db: Session = Depends(get_db)
):
    client_ip = request.client.host
    logger.info(
        f"Received request from {client_ip} for receipt # {data.receipt_number} receipt date= {data.receipt_date} receipt client= {data.receipt_client}"
    )

    existing_response = retrieve_existing_response(db, data.response_id)
    keras_label, keras_prediction = make_keras_prediction(data.encoded_receipt_file)
    logger.info(
        f"********** keras_label {keras_label} keras_prediction {keras_prediction} "
    )
    file_data = base64.b64decode(data.encoded_receipt_file)
    ocr_raw = (
        existing_response.ocr_raw if existing_response else analyze_document(file_data)
    )

    validator = get_validator(data.receipt_client)
    validator_response = validator.validate(data.model_dump(), ocr_raw)
    retval = save_response_and_return_result(
        db, ocr_raw, validator_response, keras_label, keras_prediction, data
    )
    # ReceiptApproverResponseSchema.from_orm(receipt_response)
    receipt_response_schema = ReceiptApproverResponseSchema.from_orm_with_custom_fields(
        retval
    )
    return receipt_response_schema


def retrieve_existing_response(
    db: Session, response_id: Optional[str]
) -> Optional[ReceiptApproverResponse]:
    if not response_id:
        return None

    try:
        return (
            db.query(ReceiptApproverResponse)
            .filter(ReceiptApproverResponse.id == response_id)
            .first()
        )
    except Exception as e:
        logger.warning(
            f"Failed to retrieve existing response for ID {response_id}: {e}"
        )
        return None


def make_keras_prediction(encoded_receipt_file: str):
    val = predict_receipt_type(encoded_receipt_file)
    logger.info(f"******* val =  {val}")
    keras_label, keras_prediction = predict_receipt_type(encoded_receipt_file)

    if not keras_label or keras_prediction is None:
        logger.error("Keras model prediction failed")
        raise HTTPException(status_code=500, detail="Receipt type prediction failed.")

    logger.info(
        f"Keras model predicted: {keras_label} with confidence {keras_prediction}"
    )
    return keras_label, keras_prediction


def get_validator(receipt_client: str):
    try:
        return ValidatorFactory.get_validator(receipt_client)
    except ValueError as e:
        logger.error(f"Validator not found for client: {receipt_client}, error: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@retry(wait=wait_fixed(2), stop=stop_after_attempt(3))
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
        raise e


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
        f"<<<<<<<< Engine URL: {bind_engine.url} Is Engine In-Memory: {'sqlite' in bind_engine.url.drivername and ':memory:' in str(bind_engine.url)}"
    )
    # Use SQLAlchemy inspector to get the list of tables
    inspector = inspect(bind_engine)
    tables = inspector.get_table_names()
    logger.info(f"List of Tables: {tables}")

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

    return response
