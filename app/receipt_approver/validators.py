from typing import Dict

import pandas as pd

from config.settings import settings

from .block import Block
from .utils import find_row_by_code, is_string_in_array_case_insensitive


class ReceiptValidator:
    def validate(self, input_dict: Dict, response: Dict) -> bool:
        raise NotImplementedError("Subclasses should implement this method.")


class LuxotticaReceiptValidator:
    # load luxottica SOP
    def _load_sop(self):
        # Read the Excel file
        file_path = settings.lux_sop_filepath
        print(f"<<<<<<<< sop file_path = {file_path}")
        df = pd.read_excel(file_path, sheet_name="Brand List")

        # Select specific rows and columns
        sop_df = df[["Brand", "OCR_VALUE", "Code"]]
        sop_df
        # Convert OCR_VALUE to an array of strings
        sop_df["OCR_VALUE"] = sop_df["OCR_VALUE"].apply(lambda x: [x.replace("-", "")])

        # Convert Code to an array of strings, treating '/' as a delimiter
        # sop_df["Code"] = sop_df["Code"].apply(lambda x: x.split("/"))
        sop_df["Code"] = sop_df["Code"].apply(
            lambda x: [part.strip() for part in x.split("/")]
        )

        sop_df
        return sop_df

    # validate receipt id
    def validate_receipt_number(self, sop_df, blocks, user_input_value, input_dict):
        retval = []
        print(f"user_input_receipt_number = {user_input_value}")
        for block in blocks:
            if block.block_type in ["LINE", "WORD"]:
                if block.has_value(
                    sop_df, user_input_value, input_dict, "receipt_number"
                ):
                    retval.append(block)
        return retval

    # validate receipt date
    def validate_date(self, sop_df, blocks, user_input_value, input_dict):
        print(f"validate_date called date = {user_input_value}")
        retval = []
        for block in blocks:
            if block.block_type in ["LINE", "WORD", "QUERY_RESULT"]:
                if block.has_user_input_date(user_input_value):
                    retval.append(block)
        print(f"validate_date called \n {retval} \n")
        return retval

    # validate brand
    def clean_up_user_input_brand(self, text: str) -> str:
        # Remove '- Sunglasses' and '- Optical' if present
        text = text.replace("- Sunglasses", "").replace("- Optical", "")
        return text.strip()

    def validate_brand(
        self, sop_df, blocks, user_input_value, input_dict, validated_brand_model_blocks
    ):
        user_input_value = self.clean_up_user_input_brand(user_input_value)
        print(f"validate_brand called brand = {user_input_value}")
        retval = []
        for block in blocks:
            if block.block_type in ["LINE", "WORD"]:
                if block.has_value(sop_df, user_input_value, input_dict, "brand"):
                    retval.append(block)
        if len(retval) == 0 and len(validated_brand_model_blocks) > 0:
            user_input_brand_model = input_dict["brand_model"]
            row_containing_brand_code = find_row_by_code(sop_df, user_input_brand_model)
            ocr_brand_value = row_containing_brand_code.get("OCR_VALUE", None)
            user_entered_brand = user_input_value.lower().replace("-", "")
            if ocr_brand_value and is_string_in_array_case_insensitive(
                user_entered_brand, ocr_brand_value
            ):
                retval.append(validated_brand_model_blocks[0])

        return retval

    # if not able to validate brand then validate brand via brand model
    def validate_brand_models(self, sop_df, blocks, user_input_value, input_dict):
        retval = []
        for block in blocks:
            if block.block_type in ["LINE", "WORD"]:
                if block.has_value(sop_df, user_input_value, input_dict, "brand_model"):
                    retval.append(block)
        return retval

    def validate(self, input_dict: Dict, response: Dict) -> bool:
        print("<<<<<<<< LuxotticaReceiptValidator: validate ")
        sop_df = self._load_sop()
        # print(sop_df)
        blocks = [Block(block_data) for block_data in response["Blocks"]]
        result = {}
        # date
        m_receipt_date_blocks = self.validate_date(
            sop_df, blocks, input_dict["receipt_date"], input_dict
        )
        result["receipt_date"] = {
            "user_input": input_dict["receipt_date"],
            "detected": [
                block.to_dict()
                for block in m_receipt_date_blocks  # extract_key_of_interest_from_blocks(m_receipt_date_blocks)
            ],
        }
        # receipt number
        m_receipt_number = self.validate_receipt_number(
            sop_df, blocks, input_dict["receipt_number"], input_dict
        )
        result["receipt_number"] = {
            "user_input": input_dict["receipt_number"],
            "detected": [
                block.to_dict()
                for block in m_receipt_number  # extract_key_of_interest_from_blocks(m_receipt_number)
            ],
        }
        # brand_model
        m_brand_model = self.validate_brand_models(
            sop_df, blocks, input_dict["brand_model"], input_dict
        )
        result["brand_model"] = {
            "user_input": input_dict["brand_model"],
            "detected": [
                block.to_dict()
                for block in m_brand_model  # extract_key_of_interest_from_blocks(m_brand_model)
            ],
        }
        # # brand
        m_brand = self.validate_brand(
            sop_df, blocks, input_dict["brand"], input_dict, m_brand_model
        )
        result["brand"] = {
            "user_input": input_dict["brand"],
            "detected": [block.to_dict() for block in m_brand],
        }  # extract_key_of_interest_from_blocks(m_brand)
        # Determine AI_APPROVED_STATUS based on the validation results
        if (
            result["receipt_date"]["detected"]
            and result["receipt_number"]["detected"]
            and result["brand"]["detected"]
            and len(result["receipt_date"]["detected"]) > 0
            and len(result["receipt_number"]["detected"]) > 0
            and len(result["brand"]["detected"]) > 0
        ):
            result["AI_APPROVED_STATUS"] = {"detected": "Approved"}
        else:
            result["AI_APPROVED_STATUS"] = {"detected": "Rejected"}
        # print(f"result = {result}")
        return result
