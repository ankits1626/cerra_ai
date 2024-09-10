import logging
from unittest.mock import patch

logger = logging.getLogger(__name__)


# Mock for successful keras prediction
def mock_make_keras_prediction():
    logger.info("<<<<<< mock_make_keras_prediction called")
    return patch(
        "app.receipt_approver.model_utils.predict_receipt_type",
        # "app.receipt_approver.views.make_keras_prediction",
        return_value=("Handwritten", 0.95),
    )
