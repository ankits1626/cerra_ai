import itertools
import logging
import re
from datetime import datetime

logger = logging.getLogger(__name__)


def generate_date_formats(date_str: str, input_format: str = "%Y/%m/%d") -> list:
    """Generate all possible date formats based on an input date."""
    try:
        date = datetime.strptime(date_str, input_format)

        # Year, month, and day variants
        year_variants = [date.strftime("%Y"), date.strftime("%y")]
        month_variants = [
            date.strftime("%m"),
            date.strftime("%b"),
            date.strftime("%B"),
            f"{int(date.strftime('%m'))}",  # Strip leading zeros
        ]
        day_variants = [date.strftime("%d"), f"{int(date.strftime('%d'))}"]

        # Common separators
        separators = ["-", "/", ".", " ", ","]

        # Generate all combinations
        possible_dates = set()
        for year, month, day in itertools.product(
            year_variants, month_variants, day_variants
        ):
            for sep1, sep2 in itertools.product(separators, repeat=2):
                possible_dates.update(
                    [
                        f"{year}{sep1}{month}{sep2}{day}",  # Y-M-D
                        f"{day}{sep1}{month}{sep2}{year}",  # D-M-Y
                        f"{month}{sep1}{day}{sep2}{year}",  # M-D-Y
                    ]
                )

        return sorted(possible_dates)

    except ValueError as e:
        print(f"Error generating date formats for '{date_str}': {e}")
        return []


def get_model_code(s):
    match = re.match(r"([a-zA-Z]+)(\d+)(.*)", s)
    if match:
        # Combine the second and third groups
        combined = match.group(2) + match.group(3)
        return [
            match.group(1)[:2] if len(match.group(1)) >= 2 else match.group(1),
            combined,
        ]
    else:
        return None


def find_brand_user_input(user_input):
    brand_lookup = {
        "Alain Mikli": ["Alain Mikli"],
        "Armani Exchange": ["Armani Exchange"],
        "Burberry": ["Burberry", "Burberry Junior"],
        "Chanel": ["Chanel"],
        "Coach": ["Coach"],
        "Dolce & Gabbana": ["Dolce & Gabbana"],
        "Emporio Armani": ["Emporio Armani", "Emporio Armani Kids"],
        "Giorgio Armani": ["Giorgio Armani"],
        "Michael Kors": ["Michael Kors"],
        "Miu Miu": ["Miu Miu"],
        "Oakley": [
            "Oakley",
            "Oakley Kids",
        ],
        "Oliver Peoples": [
            "Oliver Peoples",
        ],
        "Persol": ["Persol"],
        "Prada": ["Prada", "Prada Linea Rossa"],
        "Ray-Ban": [
            "Ray-Ban",
            "Rayban",
        ],
        "Starck Eyes": ["Starck Eyes"],
        "Tiffany": ["Tiffany & Co."],
        "Versace": [
            "Versace",
            "Versace Kids",
        ],
        "Vogue": ["Vogue Eyewear", "Vogue"],
        "Bvlgari": ["Bvlgari"],
        "Polo Ralph Lauren": ["Polo Ralph Lauren"],
        "Swarovski": ["Swarovski "],
        "Miraflex": ["Miraflex"],
        "Jimmy Choo": ["Jimmy Choo"],
    }

    for brand, codes in brand_lookup.items():
        if user_input in codes:
            return brand
    return None


def find_brand_by_code(code):
    brand_lookup = {
        "Alain Mikli": ["AO"],
        "Armani Exchange": ["AX"],
        "Burberry": ["BE", "JB"],
        "Chanel": ["CH"],
        "Coach": ["HC"],
        "Dolce & Gabbana": ["DG"],
        "Emporio Armani": ["EA", "EK"],
        "Giorgio Armani": ["AR", "GA"],
        "Michael Kors": ["MK"],
        "Miu Miu": ["MU"],
        "Oakley": ["OO", "SOK", "FOK", "OX", "OY", "OJF", "OK", "SOK", "OJ"],
        "Oliver Peoples": ["OV"],
        "Persol": ["PO"],
        "Prada": ["PR", "PS"],
        "Ray-Ban": ["RB", "RX", "RY", "RJ", "RW", "RJ"],
        "Starck Eyes": ["SH"],
        "Tiffany & Co.": ["TF"],
        "Versace": ["VE", "VK"],
        "Vogue": ["VO"],
        "Bvlgari": ["BV"],
        "Polo Ralph Lauren": ["PH"],
        "Swarovski": ["SK"],
        "Miraflex": ["MF"],
        "Jimmy Choo": ["JC"],
    }

    for brand, codes in brand_lookup.items():
        if code in codes:
            return brand
    return None
