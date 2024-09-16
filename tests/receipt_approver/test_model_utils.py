import base64
from io import BytesIO
from unittest import mock

import numpy as np
import pytest
from fastapi import HTTPException
from PIL import Image

from app.receipt_approver.model_utils import (
    preprocess_image_from_base64,  # Adjust the import according to your project structure
)


@pytest.fixture
def valid_base64_image():
    # Create a simple valid base64 encoded image (a blank 224x224 white image)
    img = Image.new("RGB", (224, 224), color="white")
    buffer = BytesIO()
    img.save(buffer, format="JPEG")
    img_bytes = buffer.getvalue()
    return base64.b64encode(img_bytes).decode("utf-8")


def test_preprocess_image_from_base64_valid_image(valid_base64_image):
    # Test with a valid base64 image
    img_array = preprocess_image_from_base64(valid_base64_image)

    # Check that the returned array has the expected shape and values
    assert img_array.shape == (1, 224, 224, 3)  # 1 for batch size, 224x224, 3 channels
    assert np.all(img_array <= 1.0) and np.all(
        img_array >= 0.0
    )  # Image values should be between 0 and 1


def test_preprocess_image_from_base64_invalid_base64():
    # Test with an invalid base64 image string
    invalid_base64_image = "invalid_base64_string"

    with pytest.raises(HTTPException) as exc_info:
        preprocess_image_from_base64(invalid_base64_image)

    # Check that the correct exception is raised with the correct status code and detail
    assert exc_info.value.status_code == 400
    assert exc_info.value.detail == "Invalid image format."


def test_preprocess_image_from_base64_invalid_image():
    # Test with a valid base64 string but an invalid image format (corrupted image data)
    invalid_image_data = base64.b64encode(b"not_an_image").decode("utf-8")

    with pytest.raises(HTTPException) as exc_info:
        preprocess_image_from_base64(invalid_image_data)

    # Check that the correct exception is raised with the correct status code and detail
    assert exc_info.value.status_code == 400
    assert exc_info.value.detail == "Invalid image format."


@mock.patch("app.receipt_approver.model_utils.image.img_to_array")
def test_preprocess_image_from_base64_image_processing_error(
    mock_img_to_array, valid_base64_image
):
    # Simulate an error in the image processing step (e.g., img_to_array raises an exception)
    mock_img_to_array.side_effect = Exception("Image processing error")

    with pytest.raises(HTTPException) as exc_info:
        preprocess_image_from_base64(valid_base64_image)

    # Check that the correct exception is raised with the correct status code and detail
    assert exc_info.value.status_code == 400
    assert exc_info.value.detail == "Invalid image format."
