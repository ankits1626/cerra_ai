import base64
import logging
import uuid
from datetime import datetime
from unittest.mock import patch

import pytest

from app.receipt_approver.models import ReceiptApproverResponse

from .mocks import mock_keras_prediction, mock_textract, mock_validator

logger = logging.getLogger(__name__)

# Test data
receipt_data = {
    "receipt_number": "12345",
    "receipt_client": "some_client",
    "receipt_date": "2024-09-10",
    "brand": "some_brand",
    "brand_model": "some_brand_model",
    "encoded_receipt_file": base64.b64encode(b"fake_image_data").decode("utf-8"),
}


@pytest.fixture
def mock_external_dependencies():
    """
    Conditional mocking of external dependencies like Keras, Textract, and Validator.
    """
    with mock_keras_prediction(), mock_textract(), mock_validator():
        yield
    logger.info("Teardown complete: Mocks destroyed")


def test_validate_receipt_success(client, mock_external_dependencies):
    response = client.post("/receipts/validate-receipt", json=receipt_data)
    assert response.status_code == 200
    response_json = response.json()
    assert response_json["receipt_number"] == receipt_data["receipt_number"]
    assert response_json["receipt_type"]["label"] == "Printed"
    assert response_json["validation_result"] == {"validation": "success"}


def test_validate_receipt_missing_fields(client):
    # Missing `receipt_number` and other required fields
    incomplete_data = {
        "receipt_client": "some_client",
        "encoded_receipt_file": base64.b64encode(b"fake_image_data").decode("utf-8"),
    }
    response = client.post("/receipts/validate-receipt", json=incomplete_data)

    # Assert that a 422 Unprocessable Entity error is raised
    assert response.status_code == 422


def test_validate_receipt_invalid_base64(client):
    # Invalid base64 string
    invalid_data = {
        "receipt_number": "12345",
        "receipt_client": "some_client",
        "receipt_date": "2024-09-10",
        "brand": "some_brand",
        "brand_model": "some_brand_model",
        "encoded_receipt_file": "invalid_base64_string",
    }
    response = client.post("/receipts/validate-receipt", json=invalid_data)

    # Assert the response is 400 Bad Request
    assert response.status_code == 400


def test_validate_receipt_keras_failure(client, mock_external_dependencies):
    # Conditional mocking: Simulate Keras prediction failure
    with mock_keras_prediction(success=False):
        response = client.post("/receipts/validate-receipt", json=receipt_data)
        assert response.status_code == 200
        response_json = response.json()
        assert response_json["receipt_type"] == {}


def test_validate_receipt_validator_not_found(client, mock_external_dependencies):
    with mock_validator(success=False):
        response = client.post("/receipts/validate-receipt", json=receipt_data)

        # Assert the response is 400 Bad Request

        assert response.status_code == 400
        assert response.json()["detail"] == "Invalid receipt_client"


def test_validate_receipt_textract_failure(client, mock_external_dependencies):
    # Conditional mocking: Simulate Textract failure
    with mock_textract(success=False):
        response = client.post("/receipts/validate-receipt", json=receipt_data)
        logger.info(f"******* response = {response.json()}")
        assert response.status_code == 500
        assert "Textract error" in response.json()["detail"]


@pytest.fixture
def mock_save_receipt_response():
    with patch(
        "app.receipt_approver.views.save_receipt_approver_response"
    ) as mock_save:
        yield mock_save


def test_validate_receipt_saves_in_db(
    client, mock_external_dependencies, mock_save_receipt_response
):
    # Simulate save_receipt_approver_response returning an instance of ReceiptApproverResponse
    mock_response = ReceiptApproverResponse(
        id=uuid.uuid4(),
        client="some_client",
        ocr_raw={"Blocks": [{"Text": "Sample OCR data"}]},
        processed={"validation": "success"},
        user_input_data=receipt_data,
        receipt_classifier_response={"label": "Printed", "confidence": 0.95},
        last_updated=datetime.now(),
    )
    mock_save_receipt_response.return_value = mock_response

    # Call the API
    response = client.post("/receipts/validate-receipt", json=receipt_data)

    # Assert the response is 200 OK and receipt saved successfully
    assert response.status_code == 200
    response_json = response.json()

    # Assert that the returned response matches the expected values
    assert response_json["id"] == str(mock_response.id)  # UUID to string conversion
    assert response_json["receipt_number"] == receipt_data["receipt_number"]
    assert response_json["receipt_type"]["label"] == "Printed"
    assert response_json["validation_result"] == {"validation": "success"}


def test_validate_receipt_save_failure(
    client, mock_external_dependencies, mock_save_receipt_response
):
    # Simulate a failure in saving the receipt to the database
    mock_save_receipt_response.side_effect = Exception("Database save error")

    response = client.post("/receipts/validate-receipt", json=receipt_data)

    # Assert that a 500 Internal Server Error is returned due to the save failure
    assert response.status_code == 500
    assert "Database save error" in response.json()["detail"]
