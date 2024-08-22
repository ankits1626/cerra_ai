import datetime

from dateutil import parser
from dateutil.parser import ParserError

from .utils import find_row_by_code, split_string


class Block:
    def __init__(self, block_data):
        self.id = block_data.get("Id", "")
        self.block_type = block_data.get("BlockType", "")
        self.text = block_data.get("Text", "")  # Keep original text as-is
        self.normalized_text = self.text.lower()  # Normalize text for comparison
        self.geometry = block_data.get("Geometry", {})
        # self.relationships = block_data.get("Relationships", [])

    def to_dict(self):
        # Create a copy of the geometry and remove the Polygon key if it exists
        filtered_geometry = {k: v for k, v in self.geometry.items() if k != "Polygon"}

        return {
            "id": self.id,
            "block_type": self.block_type,
            "text": self.text,
            "normalized_text": self.normalized_text,
            "geometry": filtered_geometry,
            # "relationships": self.relationships,
        }

    def __str__(self) -> str:
        return self.text

    # Check if the text is not a date
    def is_not_date(self, text):
        try:
            datetime.datetime.strptime(text, "%Y-%m-%d")  # Specify the date format here
            return False  # It is a valid date
        except ValueError:
            return True  # Not a valid date

    def reformat_ocr_date(self):
        try:
            # Extract the date part from the text by splitting on whitespace
            # Assuming date is the first part of the text
            date_part = self.text.split()[0]
            # print(f'^^^^^^^ text = {self.text} date_part = {date_part} ')

            # Return True if user_input_date is in formatted_dates
            return self.text if self.is_not_date(date_part) else date_part

        except (ValueError, OverflowError, ParserError):
            # Return False if parsing fails
            return self.text

    def has_user_input_date(self, user_input_date):
        pre = self.text
        self.text = self.reformat_ocr_date()

        try:
            # Parse the date string using dateutil.parser
            parsed_date = parser.parse(self.text, dayfirst=True)
            # Return the date formatted as 'D/M/YYYY' i.e., day/month/year
            # Format the date as 'D/M/YYYY' and 'M/D/YYYY'
            formatted_dates = [
                parsed_date.strftime("%-d/%-m/%y"),  # Day/Month/Year
                parsed_date.strftime("%-m/%-d/%y"),  # Month/Day/Year
            ]
            print(
                f"******** has_user_input_dat euser_input_date ={user_input_date} --- pre = {pre} --- text = {self.text} --- formatted_dates ={formatted_dates}"
            )
            # print(f'text = {self.text} formatted_date = {formatted_dates} user_input_date = {user_input_date}')
            return user_input_date in formatted_dates
        except (ValueError, OverflowError, ParserError):
            # Return the original date string if parsing fails
            return False

    def special_check_for_brand_models(self, value, input_dict, sop_df):
        # brands like this 7178 2001
        # print(f'<<<<<<< special_check_for_brand_models for {value}')

        splits = value.strip().split(" ")

        retval = False
        for part in splits:
            if part not in self.text:
                retval = False
                break
            else:
                retval = True

        if not retval:
            # lets check if brand models is like RB5315D
            splits = split_string(value)

            if splits and len(splits) == 2:
                row = find_row_by_code(sop_df, value)
                user_entered_brand = input_dict.get("brand", None)
                print(
                    f"~~~~~~~ splits = {splits}  user_entered_brand ={user_entered_brand}"
                )
                if row and user_entered_brand:
                    print(
                        f" row = {row} ------ user_entered_brand {user_entered_brand}"
                    )
                    user_entered_brand = user_entered_brand.lower().replace("-", "")
                    brand_matches = False

                    brands = row["OCR_VALUE"]
                    for brand in brands:
                        if brand.lower() == user_entered_brand:
                            brand_matches = True
                            break
                    code_found_in_ocr = splits[1].lower() in self.text.lower()
                    return brand_matches and code_found_in_ocr

        return retval

    def check_for_brand(self, input_dict, sop_df):
        user_input_brand = input_dict["brand"].strip()
        matching_row = sop_df[sop_df["Brand"] == user_input_brand]
        # print(
        #     f"text = {self.text.lower()} ***** user_input_brand = {user_input_brand} **** matching_row = {matching_row}"
        # )

        ocr_brands = matching_row["OCR_VALUE"].values.tolist()

        if len(ocr_brands) > 0:
            ocr_brands = matching_row["OCR_VALUE"].values.tolist()[0]

        else:
            return False
        ocr_brands = [elem.lower() for elem in ocr_brands]

        for brand in ocr_brands:
            if brand.lower() in self.text.lower():
                print(
                    f"text = {self.text.lower()} ***** user_input_brand = {user_input_brand} **** ocr_brands = {ocr_brands}"
                )
                return True
        return False

    def has_value(self, sop_df, value, input_dict=None, key=None):
        original_value = value
        text = self.normalized_text.replace(" ", "").replace("-", "").lower()
        if self.is_not_date(text):
            text = text.replace("/", "")

        value = value.replace("-", "").replace(" ", "").lower()
        # if value == 'poc24005199':
        #     print(f'value = {value}, text ={text} match = {value in text}')
        retval = value in text
        if key == "brand_model" and not retval:
            return self.special_check_for_brand_models(
                original_value, input_dict, sop_df
            )

        if key == "brand" and not retval:
            return self.check_for_brand(input_dict, sop_df)
        return retval

    def get_bounding_box(self, image_width, image_height):
        bounding_box = self.geometry.get("BoundingBox", {})
        # image_width = 800  # Example image width (replace with actual image width)
        # image_height = 600  # Example image height (replace with actual image height)

        left = bounding_box.get("Left", 0.0) * image_width
        top = bounding_box.get("Top", 0.0) * image_height
        width = bounding_box.get("Width", 0.0) * image_width
        height = bounding_box.get("Height", 0.0) * image_height

        return left, top, width, height
