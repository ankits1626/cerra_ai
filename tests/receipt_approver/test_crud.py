import logging

from app.receipt_approver.crud import (
    create_user_input_data,
    get_existing_response,
    save_receipt_approver_response,
)
from app.receipt_approver.models import ReceiptApproverResponse
from app.receipt_approver.schemas import ReceiptData

logger = logging.getLogger(__name__)


def test_create_user_input_data():
    # Mock receipt_data
    receipt_data = ReceiptData(
        receipt_id="1234",
        receipt_number="123",
        receipt_date="2024-09-01",
        brand="BrandX",
        encoded_receipt_file="test",
        receipt_client="test",
        brand_model="ModelY",
        response_id=None,
    )

    # Call the function
    result = create_user_input_data(receipt_data)
    logger.info(f"result = {result}")
    # Check the result
    assert result == {
        "receipt_id": 1234,
        "receipt_number": "123",
        "receipt_date": "2024-09-01",
        "brand": "BrandX",
        "brand_model": "ModelY",
    }


def test_get_existing_response(test_db):
    # Insert mock data into the test database
    new_response = ReceiptApproverResponse(
        receipt_id=123456,
        client="clientX",
        ocr_raw={"key": "value"},
        processed={"key": "processed_value"},
        user_input_data={"receipt_number": "123", "brand": "BrandX"},
        receipt_classifier_response={"result": "mock_classifier"},
    )
    test_db.add(new_response)
    test_db.commit()

    # Test if get_existing_response returns the correct result
    response = get_existing_response(test_db, new_response.receipt_id)
    logger.info(f"response = {response}")
    assert response.receipt_id == new_response.receipt_id
    assert response.client == "clientX"
    assert response.ocr_raw == {"key": "value"}
    assert response.processed == {"key": "processed_value"}
    assert response.user_input_data == {"receipt_number": "123", "brand": "BrandX"}
    assert response.receipt_classifier_response == {"result": "mock_classifier"}
    assert response.last_updated is not None


def test_save_receipt_approver_response_new(test_db):
    # Mock receipt_data
    receipt_data = ReceiptData(
        receipt_id=1234567,
        receipt_number="123",
        receipt_date="2024-09-01",
        brand="BrandX",
        encoded_receipt_file="str",
        receipt_client="clientX",
        brand_model="ModelY",
        response_id=None,
    )

    # Call the main function to test
    response = save_receipt_approver_response(
        db=test_db,
        ocr_raw={"ocr": "data"},
        processed={"processed": "data"},
        client="clientX",
        receipt_data=receipt_data,
        receipt_classifier_response={"classifier": "result"},
    )

    # Assert that the object is created and stored in the database
    assert response is not None
    assert isinstance(response, ReceiptApproverResponse)
    assert response.ocr_raw == {"ocr": "data"}

    # Check that it was added to the database
    saved_response = test_db.query(ReceiptApproverResponse).first()
    assert saved_response is not None
    assert saved_response.ocr_raw == {"ocr": "data"}
    assert saved_response.client == "clientX"


def test_save_receipt_approver_response_update(test_db):
    # Create an existing response in the database
    existing_response = ReceiptApproverResponse(
        receipt_id=12345678,
        ocr_raw={"ocr": "old_data"},
        processed={"processed": "old_data"},
        client="clientX",
        user_input_data={
            "receipt_number": "123",
            "receipt_date": "2024-09-01",
            "brand": "BrandX",
            "brand_model": "ModelY",
        },
        receipt_classifier_response={"classifier": "old_result"},
    )
    test_db.add(existing_response)
    test_db.commit()
    logger.info(f"existing_response = {existing_response}")
    # Mock receipt_data
    receipt_data = ReceiptData(
        receipt_number="123",
        receipt_date="2024-09-01",
        brand="BrandX",
        encoded_receipt_file="str",
        receipt_client="clientY",
        brand_model="ModelY",
        receipt_id=existing_response.receipt_id,
    )

    # Call the main function to update the existing response
    response = save_receipt_approver_response(
        db=test_db,
        ocr_raw={"ocr": "new_data"},
        processed={"processed": "new_data"},
        client="clientY",
        receipt_data=receipt_data,
        receipt_classifier_response={"classifier": "new_result"},
    )

    # Assert that the object was updated
    assert response is not None
    assert response.ocr_raw == {"ocr": "new_data"}

    # Verify that the response in the database was updated
    updated_response = (
        test_db.query(ReceiptApproverResponse)
        .filter_by(receipt_id=existing_response.receipt_id)
        .first()
    )
    assert updated_response is not None
    assert updated_response.ocr_raw == {"ocr": "new_data"}
    assert updated_response.client == "clientY"
