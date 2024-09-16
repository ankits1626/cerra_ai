import pytest

from app.receipt_approver.block import Block

# Sample Block data with bounding box geometry
sample_block_data = {
    "Id": "123",
    "BlockType": "LINE",
    "Text": "Sample text",
    "Geometry": {
        "BoundingBox": {
            "Left": 0.1,  # 10% from the left
            "Top": 0.2,  # 20% from the top
            "Width": 0.5,  # 50% of the image width
            "Height": 0.3,  # 30% of the image height
        }
    },
}


def test_get_bounding_box():
    # Arrange
    block = Block(sample_block_data)
    image_width = 1000  # Example image width
    image_height = 800  # Example image height

    # Act
    left, top, width, height = block.get_bounding_box(image_width, image_height)

    # Assert - Expected values based on image size and bounding box
    assert left == 100.0  # 10% of 1000
    assert top == 160.0  # 20% of 800
    assert width == 500.0  # 50% of 1000
    assert height == 240.0  # 30% of 800


def test_get_bounding_box_invalid_image_size():
    # Arrange
    block = Block(sample_block_data)

    # Act & Assert - Invalid image dimensions
    with pytest.raises(ValueError):
        block.get_bounding_box(0, 800)  # Invalid width
    with pytest.raises(ValueError):
        block.get_bounding_box(1000, 0)  # Invalid height
    with pytest.raises(ValueError):
        block.get_bounding_box(-1000, 800)  # Negative width


def test_block_str():
    # Arrange
    block = Block(sample_block_data)

    # Act
    result = str(block)

    # Assert
    assert result == "Sample text"
