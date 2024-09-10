import logging
from unittest.mock import patch

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)

logger = logging.getLogger(__name__)

# Test data

# class ReceiptData(BaseModel):
#     receipt_number: str
#     receipt_date: str
#     brand: str
#     encoded_receipt_file: str
#     receipt_client: str
#     brand_model: str
#     response_id: Optional[UUID] = None
receipt_data = {
    "receipt_number": "12345",
    "receipt_client": "some_client",
    "receipt_date": "2024-09-10",
    "brand": "some_brand",
    "brand_model": "some_brand_model",
    "encoded_receipt_file": "test",  # base64.b64encode(b"fake_image_data").decode("utf-8"),
}


# Mock for Keras prediction function
@patch("app.receipt_approver.views.get_validator")
@patch("app.receipt_approver.views.analyze_document")
@patch("app.receipt_approver.views.predict_receipt_type")
def test_validate_receipt_success(
    mock_predict_receipt_type,
    mock_analyze_document,
    mock_get_validator,
    client,
    test_db,
):
    # Mock the Keras model prediction and AWS Textract response
    mock_predict_receipt_type.return_value = ("Printed", 0.95)
    mock_analyze_document.return_value = {"Blocks": [{"Text": "Sample OCR data"}]}
    # Mock a dummy validator with a validate method
    mock_validator = mock_get_validator.return_value
    mock_validator.validate.return_value = {"validation": "success"}

    # Call the API
    response = client.post("receipts/validate-receipt", json=receipt_data)

    # Assert the response status and structure
    assert response.status_code == 200
    response_json = response.json()
    logger.info(f"******** response_json = {response_json}")
    assert response_json["receipt_number"] == receipt_data["receipt_number"]
    assert response_json["receipt_type"]["label"] == "Printed"
    assert response_json["validation_result"] == {"validation": "success"}
