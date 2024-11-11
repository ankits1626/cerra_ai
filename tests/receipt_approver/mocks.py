import logging
from unittest.mock import MagicMock, patch

from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)


def mock_keras_prediction(success=True):
    """
    Mocks the Keras prediction. If success is False, return None values to simulate a failure.
    """
    # mock_textract_client = MagicMock()
    if success:
        return patch(
            "app.receipt_approver.views.predict_receipt_type",
            return_value=("Printed", 0.95) if success else (None, None),
        )
    else:
        return patch(
            "app.receipt_approver.views.predict_receipt_type",
            side_effect=ValueError("Invalid receipt_client"),
        )


def mock_textract(success=True):
    """
    Mocks the AWS Textract response. If success is False, raises an Exception.
    """
    mock_textract_client = MagicMock()
    if success:
        logger.info("<<<<<<<<<< using success boto patch")
        mock_textract_client.analyze_document.return_value = {
            "Blocks": [
                {"BlockType": "LINE", "Text": "Sample OCR data"},
                {"BlockType": "LINE", "Text": "Date: 2023-09-01"},
            ]
        }
    else:
        logger.info("<<<<<<<<<< using failed boto patch")
        error_response = {
            "Error": {"Code": "InvalidDocument", "Message": "Textract failed"}
        }

        mock_textract_client.analyze_document.side_effect = ClientError(
            error_response, "analyze_document"
        )

    return patch("boto3.client", return_value=mock_textract_client)


def mock_validator(success=True):
    """
    Mocks the Validator. If success is False, raises a ValueError for missing client.
    """
    if success:
        return patch(
            "app.receipt_approver.validator_factory.ValidatorFactory.get_validator",
            return_value=MockValidator(),
        )
    else:
        return patch(
            "app.receipt_approver.validator_factory.ValidatorFactory.get_validator",
            side_effect=ValueError("Invalid receipt_client"),
        )


class MockValidator:
    def validate(self, *args, **kwargs):
        return {"validation": "success"}


class MockTextractClient:
    def analyze_document(self, **kwargs):
        return {
            "Blocks": [
                {"BlockType": "LINE", "Text": "Sample OCR data"},
                {"BlockType": "LINE", "Text": "Date: 2023-09-01"},
            ]
        }
