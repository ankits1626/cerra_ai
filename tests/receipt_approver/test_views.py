import base64
import logging
from datetime import datetime
from unittest.mock import patch

import pytest

from app.receipt_approver.models import ReceiptApproverResponse

from .mocks import mock_keras_prediction, mock_textract, mock_validator

logger = logging.getLogger(__name__)

# Test data
receipt_data = {
    "receipt_id": 12222,
    "receipt_number": "12345",
    "receipt_client": "some_client",
    "receipt_date": "2024-09-10",
    "brand": "some_brand",
    "brand_model": "some_brand_model",
    "encoded_receipt_file": base64.b64encode(b"fake_image_data").decode("utf-8"),
}


def create_existing_receipt_response(db_session):
    """
    Creates an existing ReceiptApproverResponse in the database.
    """
    existing_response = ReceiptApproverResponse(
        receipt_id=receipt_data["receipt_id"],
        client=receipt_data["receipt_client"],
        user_input_data=receipt_data,
        ocr_raw={"ocr_data": "fake_ocr_data"},
        processed={"ai_inference": "fake_inference_data"},
        receipt_classifier_response={"label": "Printed", "confidence": 0.95},
    )
    db_session.add(existing_response)
    db_session.commit()
    return existing_response


@pytest.fixture
def mock_external_dependencies():
    """
    Conditional mocking of external dependencies like Keras, Textract, and Validator.
    """
    with mock_keras_prediction(), mock_textract(), mock_validator():
        yield
    logger.info("Teardown complete: Mocks destroyed")


@pytest.fixture
def mock_external_dependencies_excluding():
    """
    Conditional mocking of external dependencies like Keras, Textract, and Validator.
    """
    with mock_keras_prediction(), mock_textract():
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
        "receipt_id": 1212,
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
    assert response.json()["detail"] == "Encoded image is Invalid."


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
    receipt_data["receipt_id"] = 1111
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
        receipt_id=121314,
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
    assert response_json["receipt_id"] == mock_response.receipt_id
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


def test_validate_receipt_with_existing_response(
    client, test_db, mock_external_dependencies
):
    """
    Test case where the validate_receipt fetches an existing response from the database.
    """
    # Create an existing receipt approver response in the database
    existing_response = create_existing_receipt_response(test_db)

    # Include the response_id in the request payload to simulate fetching the existing response
    receipt_data_with_receipt_id = receipt_data.copy()
    receipt_data_with_receipt_id["receipt_id"] = existing_response.receipt_id

    # Make the request
    response = client.post(
        "/receipts/validate-receipt", json=receipt_data_with_receipt_id
    )

    # Assertions
    assert response.status_code == 200
    response_json = response.json()
    assert response_json["receipt_number"] == receipt_data["receipt_number"]
    assert (
        response_json["receipt_type"]["label"] == "Printed"
    )  # Mocked value from keras
    assert response_json["validation_result"] == {
        "validation": "success"
    }  # Existing validation result


def test_validate_receipt_exception_during_retrieve_existing_response(
    client, mock_external_dependencies
):
    """
    Test case where an exception is raised while retrieving an existing response.
    """
    # Mocking the `db.query().filter().first()` to raise an exception
    with patch("sqlalchemy.orm.Session.query") as mock_query:
        mock_query.side_effect = Exception("Database retrieval error")

        # Make the request
        receipt_data_with_response_id = receipt_data.copy()
        receipt_data_with_response_id["receipt_id"] = 45637
        # receipt_data_with_response_id["response_id"] = str(
        #     uuid.uuid4()
        # )  # Simulate a response_id in the request

        response = client.post(
            "/receipts/validate-receipt", json=receipt_data_with_response_id
        )

        # Assertions
        assert (
            response.status_code == 200
        )  # The API should handle the exception and still proceed
        response_json = response.json()
        assert response_json["receipt_number"] == receipt_data["receipt_number"]
        assert (
            response_json["receipt_type"]["label"] == "Printed"
        )  # Mocked value from keras
        assert response_json["validation_result"] == {"validation": "success"}
        logger.warning("Database retrieval error handled successfully.")


def test_validate_receipt_exception_in_keras_prediction(
    client, test_db, mock_external_dependencies
):
    """
    Test case where an exception is raised in the `make_keras_prediction` function.
    """
    # Mocking the `predict_receipt_type` to raise an exception
    # with patch(
    #     "app.receipt_approver.model_utils.predict_receipt_type"
    # ) as mock_keras_prediction:
    with mock_keras_prediction(success=False):
        mock_keras_prediction.side_effect = Exception("Keras prediction error")

        # Make the request
        response = client.post("/receipts/validate-receipt", json=receipt_data)

        # Assertions
        response_json = response.json()
        logger.info(f"<<<<<<<<< response_json ={response_json}")
        assert response.status_code == 200

        assert response_json["validation_result"] == {"validation": "success"}


def test_invalid_client_error(client, mock_external_dependencies_excluding):
    response = client.post("/receipts/validate-receipt", json=receipt_data)
    assert response.status_code == 400
    assert response.json()["detail"] == "Invalid receipt_client"
