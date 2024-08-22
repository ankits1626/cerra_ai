import re


def is_string_in_array_case_insensitive(string, array):
    return any(string.lower() == elem.lower() for elem in array)


def split_string(s):
    match = re.match(r"([a-zA-Z]+)(\d+)(.*)", s)
    if match:
        # Combine the second and third groups
        combined = match.group(2) + match.group(3)
        return [match.group(1), combined]
    else:
        return None


def find_row_by_code(df, text):
    split_result = split_string(text)
    print(f"find_row_by_code text = {text} split_result ={split_result}")
    if split_result:
        extracted_code = split_result[0].upper()
        # matching_row = df[df["Code"].apply(lambda x: extracted_code in x)]
        matching_row = df[df["Code"].apply(lambda x: print(x) or extracted_code in x)]
        print(
            f"find_row_by_code text = {text} split_result ={split_result} matching_row ={matching_row}"
        )
        if not matching_row.empty:
            return {
                "OCR_VALUE": matching_row["OCR_VALUE"].values.tolist()[0],
                "Code": matching_row["Code"].values.tolist()[0],
            }
        else:
            return {"OCR_VALUE": [], "Code": []}
    else:
        return {"OCR_VALUE": [], "Code": []}
