import pytest

from app.receipt_approver.validators import LuxotticaReceiptValidator

# Sample blocks data
sample_blocks = [
    {"BlockType": "LINE", "Text": "Rayban", "NormalizedText": "Rayban"},
    {"BlockType": "WORD", "Text": "01/01/2023", "NormalizedText": "01/01/2023"},
    {"BlockType": "LINE", "Text": "123456789", "NormalizedText": "123456789"},
]


# Fixtures
@pytest.fixture
def user_input_dict():
    return {
        "receipt_date": "01/01/23",
        "receipt_number": "123456789",
        "brand": "Rayban",
        "brand_model": "rb7178",
    }


@pytest.fixture
def general_response_data():
    return {"Blocks": sample_blocks}


@pytest.fixture
def response_data_with_brand_model():
    return {
        "Blocks": [
            {"BlockType": "LINE", "Text": "rb7178", "NormalizedText": "rb7178"},
            {"BlockType": "WORD", "Text": "01/01/2023", "NormalizedText": "01/01/2023"},
            {"BlockType": "LINE", "Text": "123456789", "NormalizedText": "123456789"},
        ]
    }


@pytest.fixture
def validator_instance(
    user_input_dict,
    general_response_data,
):
    return LuxotticaReceiptValidator(user_input_dict, general_response_data)


@pytest.fixture
def validator_instance_for_brand_model(user_input_dict, response_data_with_brand_model):
    return LuxotticaReceiptValidator(user_input_dict, response_data_with_brand_model)


# Test cases
def test_initialize_validator(
    validator_instance, user_input_dict, general_response_data
):
    assert validator_instance.user_input_dict == user_input_dict
    assert len(validator_instance.blocks) == len(general_response_data["Blocks"])


def test_validate_receipt_number(validator_instance):
    result = validator_instance.validate_receipt_number()
    assert len(result) == 1
    assert result[0].normalized_text == "123456789"


def test_validate_date(validator_instance):
    result = validator_instance.validate_date()
    assert len(result) == 1
    assert result[0].normalized_text == "01/01/2023"


def test_validate_brand(validator_instance):
    result = validator_instance.validate_brand([])
    assert len(result) == 1
    assert result[0].normalized_text == "rayban"


def test_validate_brand_model(validator_instance_for_brand_model):
    result = validator_instance_for_brand_model.validate_brand_models()
    assert len(result) == 1
    assert result[0].normalized_text == "rb7178"


def test_validate_brand_via_brand_model(validator_instance_for_brand_model):
    result = validator_instance_for_brand_model.validate_brand_models()
    result = validator_instance_for_brand_model.validate_brand(result)
    assert len(result) == 1
    assert result[0].normalized_text == "rb7178"


def test_complete_validation(validator_instance):
    result = validator_instance.validate()
    print(f"result = {result}")
    assert result["receipt_number"]["detected"]
    assert result["receipt_date"]["detected"]
    assert result["brand"]["detected"]
    assert result["AI_APPROVED_STATUS"]["detected"] == "Approved"


# Negative test cases


def test_invalid_receipt_number(validator_instance):
    # Change receipt number to something invalid
    validator_instance.user_input_dict["receipt_number"] = "000000000"
    result = validator_instance.validate_receipt_number()
    assert len(result) == 0  # No blocks should be detected for invalid receipt number


def test_invalid_receipt_date(validator_instance):
    # Change receipt date to something invalid
    validator_instance.user_input_dict["receipt_date"] = "31/12/99"
    result = validator_instance.validate_date()
    assert len(result) == 0  # No blocks should be detected for invalid receipt date


def test_invalid_brand(validator_instance):
    # Change brand to something invalid
    validator_instance.user_input_dict["brand"] = "InvalidBrand"
    result = validator_instance.validate_brand([])
    assert len(result) == 0  # No blocks should be detected for invalid brand


def test_partial_validation_fail(validator_instance):
    # Invalidate the brand and test full validation
    validator_instance.user_input_dict["brand"] = "InvalidBrand"
    result = validator_instance.validate()

    assert result["receipt_number"][
        "detected"
    ]  # Receipt number should still be detected
    assert result["receipt_date"]["detected"]  # Receipt date should still be detected
    assert not result["brand"]["detected"]  # Brand should not be detected
    assert (
        result["AI_APPROVED_STATUS"]["detected"] == "Rejected"
    )  # Validation should fail


def test_complete_validation_fail(validator_instance):
    # Invalidate all fields and test full validation
    validator_instance.user_input_dict["receipt_number"] = "000000000"
    validator_instance.user_input_dict["receipt_date"] = "31/12/99"
    validator_instance.user_input_dict["brand"] = "InvalidBrand"

    result = validator_instance.validate()

    assert not result["receipt_number"][
        "detected"
    ]  # No receipt number should be detected
    assert not result["receipt_date"]["detected"]  # No receipt date should be detected
    assert not result["brand"]["detected"]  # No brand should be detected
    assert result["AI_APPROVED_STATUS"]["detected"] == "Rejected"
