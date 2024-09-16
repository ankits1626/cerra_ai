from typing import Dict, List

from app.config.settings import settings

from .block import Block
from .utils import (
    find_brand_by_code,
    find_brand_user_input,
    generate_date_formats,
    get_model_code,
)


class ReceiptValidator:
    def validate(self) -> bool:
        raise NotImplementedError("Subclasses should implement this method.")


class LuxotticaReceiptValidator(ReceiptValidator):
    def __init__(self, user_input_dict: Dict, response: Dict) -> None:
        self.user_input_dict = user_input_dict
        self.blocks = [Block(block_data) for block_data in response["Blocks"]]

    def _normalize_text(self, text: str) -> str:
        """Normalize text by removing spaces, dashes, and converting to lowercase."""
        return text.replace(" ", "").replace("-", "").replace("/", "").lower()

    def _get_matching_blocks(
        self, normalized_value: str, block_types: List[str]
    ) -> List[Block]:
        """Return blocks where the normalized text matches the provided value."""
        return [
            block
            for block in self.blocks
            if block.block_type in block_types
            and normalized_value in self._normalize_text(block.normalized_text)
        ]

    def _validate_field(self, field_key: str, block_types: List[str]) -> List[Block]:
        """Generic validation method for fields like receipt number, brand model, etc."""
        normalized_field_value = self._normalize_text(self.user_input_dict[field_key])
        return self._get_matching_blocks(normalized_field_value, block_types)

    # Validate receipt number
    def validate_receipt_number(self) -> List[Block]:
        return self._validate_field("receipt_number", ["LINE", "WORD"])

    # Validate receipt date
    def validate_date(self) -> List[Block]:
        user_entered_date_variations = generate_date_formats(
            self.user_input_dict["receipt_date"],
            input_format=settings.lux_receipt_date_format,
        )
        return [
            block
            for block in self.blocks
            if block.block_type in ["LINE", "WORD", "QUERY_RESULT"]
            and any(
                variation in block.text.replace(", ", ",").replace("/ ", "/")
                for variation in user_entered_date_variations
            )
        ]

    # Clean up brand input
    def clean_up_user_input_brand(self, text: str) -> str:
        return text.replace("- Sunglasses", "").replace("- Optical", "").strip()

    # Validate brand
    def validate_brand(self, validated_brand_model_blocks: List[Block]) -> List[Block]:
        """Validate the brand by comparing the user input and checking for matches."""
        user_input_brand = self.clean_up_user_input_brand(self.user_input_dict["brand"])
        brand = find_brand_user_input(user_input_brand)

        if brand:
            normalized_user_input_brand = self._normalize_text(brand)

            # Find matching blocks for the normalized user input brand
            matching_blocks = self._get_matching_blocks(
                normalized_user_input_brand, ["LINE", "WORD"]
            )

            # If no matching blocks are found and there are validated brand model blocks, check for model-based brand codes
            if not matching_blocks and validated_brand_model_blocks:
                for model_block in validated_brand_model_blocks:
                    model_code_splits = get_model_code(model_block.text)

                    # Ensure that model_code_splits is not empty or None
                    if model_code_splits:
                        brand_code = model_code_splits[0].upper()
                        brand_from_code = find_brand_by_code(brand_code)

                        # If a brand is found via the brand code and it matches the user input brand, return the model block
                        if (
                            brand_from_code
                            and self._normalize_text(brand_from_code)
                            == normalized_user_input_brand
                        ):
                            return [model_block]

            return matching_blocks
        else:
            return []

    # Validate brand models
    def validate_brand_models(self) -> List[Block]:
        return self._validate_field("brand_model", ["LINE", "WORD"])

    # Validate all fields and return results
    def validate(self) -> Dict:
        validated_brands = self.validate_brand_models()
        result = {
            "receipt_date": {
                "user_input": self.user_input_dict["receipt_date"],
                "detected": [block.to_dict() for block in self.validate_date()],
            },
            "receipt_number": {
                "user_input": self.user_input_dict["receipt_number"],
                "detected": [
                    block.to_dict() for block in self.validate_receipt_number()
                ],
            },
            "brand_model": {
                "user_input": self.user_input_dict["brand_model"],
                "detected": [block.to_dict() for block in validated_brands],
            },
            "brand": {
                "user_input": self.user_input_dict["brand"],
                "detected": [
                    block.to_dict() for block in self.validate_brand(validated_brands)
                ],
            },
        }

        # Determine AI_APPROVED_STATUS
        result["AI_APPROVED_STATUS"] = {
            "detected": "Approved"
            if all(
                result[key]["detected"]
                for key in ["receipt_date", "receipt_number", "brand"]
            )
            else "Rejected"
        }

        return result
