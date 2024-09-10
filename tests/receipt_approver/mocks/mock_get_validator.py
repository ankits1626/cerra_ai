from unittest.mock import MagicMock, patch


# Mock for successful validator retrieval
def mock_get_validator_success():
    return patch(
        "app.receipt_approver.validator_factory.ValidatorFactory.get_validator",
        return_value=MagicMock(validate=lambda x, y: {"validation": "passed"}),
    )


# Mock for validator retrieval error
def mock_get_validator_error():
    return patch(
        "app.receipt_approver.validator_factory.ValidatorFactory.get_validator",
        side_effect=ValueError("Validator not found"),
    )
