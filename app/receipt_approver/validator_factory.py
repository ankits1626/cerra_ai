from typing import Type

from .validators import LuxotticaReceiptValidator, ReceiptValidator


class ValidatorFactory:
    @staticmethod
    def get_validator(receipt_client: str) -> Type[ReceiptValidator]:
        print(f"ValidatorFactory: get_validator receipt_client ={receipt_client}")
        if receipt_client == "Luxottica":
            return LuxotticaReceiptValidator()
        else:
            raise ValueError("Invalid receipt_client")
