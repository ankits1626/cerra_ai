import uuid

from app.receipt_approver.models import ReceiptApproverResponse


def test_db_connection(test_db):
    # Verify that the database is empty
    results = test_db.query(ReceiptApproverResponse).all()
    assert len(results) == 0

    # Insert a test record
    new_receipt = ReceiptApproverResponse(
        id=uuid.uuid4(),
        client="Test Client",
        ocr_raw={"raw_data": "test_ocr"},
        processed={"processed_data": "test_processed"},
        user_input_data={"input_data": "test_user_input"},
        receipt_classifier_response=None,
    )

    test_db.add(new_receipt)
    test_db.commit()

    # Query the inserted record
    result = (
        test_db.query(ReceiptApproverResponse).filter_by(client="Test Client").first()
    )

    # Verify the result
    assert result is not None
    assert result.client == "Test Client"
    assert result.ocr_raw["raw_data"] == "test_ocr"
    assert result.processed["processed_data"] == "test_processed"
    assert result.user_input_data["input_data"] == "test_user_input"
    assert result.receipt_classifier_response is None
