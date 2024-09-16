from app.receipt_approver.validator_factory import ValidatorFactory
from app.receipt_approver.validators import LuxotticaReceiptValidator

mock_response = {
    "Blocks": [
        {"some_block_data": "value1"},
        {"some_block_data": "value2"},
    ]
}


def test_luxottica_should_be_received():
    factory = ValidatorFactory.get_validator("Luxottica", {}, mock_response)
    assert isinstance(factory, LuxotticaReceiptValidator)
