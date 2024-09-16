from typing import Dict, Type

from .validators import LuxotticaReceiptValidator, ReceiptValidator


class ValidatorFactory:
    @staticmethod
    def get_validator(
        receipt_client: str, user_input: Dict, response: Dict
    ) -> Type[ReceiptValidator]:
        if receipt_client == "Luxottica":
            return LuxotticaReceiptValidator(user_input, response)
        else:
            raise ValueError("Invalid receipt_client")
