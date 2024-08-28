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
        if data.response_id:
            existing_response = (
                db.query(ReceiptApproverResponse)
                .filter(ReceiptApproverResponse.id == data.response_id)
                .first()
            )
        # Decode the base64 encoded file
        file_data = base64.b64decode(data.encoded_receipt_file)
        receipt_date = data.receipt_date
        if existing_response:
            ocr_raw = existing_response.ocr_raw
        else:
            # Initialize boto3 client for Textract
            boto_client = boto3.client(
                "textract",
                region_name=settings.OCR_AWS_REGION_NAME,
                aws_access_key_id=settings.OCR_AWS_ACCESS_KEY_ID,
                aws_secret_access_key=settings.OCR_AWS_SECRET_ACCESS_KEY,
            )

            # # Call Textract analyze_document
            try:
                ocr_raw = boto_client.analyze_document(
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
                error_code = e.response["ResponseMetadata"]["HTTPStatusCode"]
                error_message = e.response["Error"]["Message"]
                print(f"<<<<< BotoCoreError = {error_message}")
                raise HTTPException(status_code=error_code, detail=error_message)

        # Get the appropriate validator
        try:
            validator = ValidatorFactory.get_validator(data.receipt_client)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))

        # Validate the Textract response
        validator_response = validator.validate(data.dict(), ocr_raw)
        # print(
        #     f"<<<<< validator_response = {validator_response} - {not validator_response}"
        # )
        # if not validator_response:
        #     raise HTTPException(
        #         status_code=400, detail="Validation failed for receipt client."
        #     )
        response = save_receipt_approver_response(
            db, ocr_raw, validator_response, data.receipt_client, data
        )

        response = {
            "id": str(response.id),
            "receipt_number": data.receipt_number,
            "receipt_date": data.receipt_date,
            "brand": data.brand,
            "status": "success",
            "validation_result": validator_response,
            "message": "File processed successfully.",
            "last_updated": response.last_updated,
        }
        return response
    except Exception as e:
        print(f"<<<<< this error  = {e}")
        raise HTTPException(status_code=500, detail=str(e))
