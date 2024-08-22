import base64
import os
from typing import Dict

import boto3
from botocore.exceptions import BotoCoreError, ClientError
from fastapi import APIRouter, HTTPException

from .schemas import ReceiptData
from .validator_factory import ValidatorFactory

router = APIRouter()


@router.post("/validate-receipt")
def validate_receipt(data: ReceiptData) -> Dict:
    print(f"<<<<<<<< updated receipt # = {data.receipt_number}")
    print(f"<<<<<<<< receipt client= {data.receipt_client}")
    print(f"<<<<<<<< receipt date= {data.receipt_date}")
    # Get AWS credentials from environment variables
    aws_region = os.getenv("OCR_AWS_REGION_NAME")
    aws_access_key_id = os.getenv("OCR_AWS_ACCESS_KEY_ID")
    aws_secret_access_key = os.getenv("OCR_AWS_SECRET_ACCESS_KEY")
    print(f"<<<<<<<< aws_region= {aws_region}")
    print(f"<<<<<<<< aws_access_key_id= {aws_access_key_id}")
    print(f"<<<<<<<< aws_secret_access_key= {aws_secret_access_key}")

    try:
        # Decode the base64 encoded file
        file_data = base64.b64decode(data.encoded_receipt_file)
        receipt_date = data.receipt_date

        # Initialize boto3 client for Textract
        boto_client = boto3.client(
            "textract",
            region_name=os.getenv("OCR_AWS_REGION_NAME"),
            aws_access_key_id=os.getenv("OCR_AWS_ACCESS_KEY_ID"),
            aws_secret_access_key=os.getenv("OCR_AWS_SECRET_ACCESS_KEY"),
        )

        # # Call Textract analyze_document
        try:
            response = boto_client.analyze_document(
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
        validator_response = validator.validate(data.dict(), response)
        print(
            f"<<<<< validator_response = {validator_response} - {not validator_response}"
        )
        # if not validator_response:
        #     raise HTTPException(
        #         status_code=400, detail="Validation failed for receipt client."
        #     )

        response = {
            "receipt_number": data.receipt_number,
            "receipt_date": data.receipt_date,
            "brand": data.brand,
            "status": "success",
            "validation_result": validator_response,
            "message": "File processed successfully.",
        }
        return response
    except Exception as e:
        print(f"<<<<< this error  = {e}")
        raise HTTPException(status_code=500, detail=str(e))
