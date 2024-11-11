from app.receipt_approver.utils import (
    find_brand_by_code,
    generate_date_formats,
    get_model_code,
)


def test_invalid_date():
    invalid_date_str = "2023/09/31"  # Invalid date

    result = generate_date_formats(invalid_date_str)

    assert result == []  # Expecting an empty li


def test_get_mode_code_for_valid_code():
    result = get_model_code("rb732")
    print(f"result = {result}")
    assert len(result) > 0
    assert result[0] == "rb"


def test_get_mode_code_for_invalid_code():
    result = get_model_code("732")
    assert result is None


def test_find_brand_by_code_for_valid_code():
    result = get_model_code("rb732")
    print
    result = find_brand_by_code(result[0].upper())
    assert result == "Ray-Ban"


def test_find_brand_by_code_for_invalid_code():
    result = find_brand_by_code("xyz")
    assert result is None
