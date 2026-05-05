"""ASIN format validation utilities."""

import re

# Amazon ASINs are exactly 10 characters: start with B or a digit, then alphanumeric
_ASIN_PATTERN = re.compile(r"^[B0-9][A-Z0-9]{9}$")


def is_valid_asin(asin: str) -> bool:
    """Return True if the string is a valid Amazon ASIN format.

    Rules:
    - Exactly 10 characters
    - Starts with 'B' or a digit (0-9)
    - All remaining characters are uppercase alphanumeric
    """
    return bool(_ASIN_PATTERN.match(asin.strip().upper()))


def validate_asins(your_asin: str, competitor_asins: list[str]) -> list[str]:
    """Validate all ASINs and return a list of error messages.

    Returns an empty list if everything is valid.
    """
    errors: list[str] = []

    if not your_asin:
        errors.append("Your product ASIN is required.")
    elif not is_valid_asin(your_asin):
        errors.append(
            f"'{your_asin}' is not a valid ASIN. "
            "ASINs are 10 characters, start with B or a digit, and are alphanumeric."
        )

    if len(competitor_asins) > 3:
        errors.append("A maximum of 3 competitor ASINs are allowed.")

    for asin in competitor_asins:
        if not is_valid_asin(asin):
            errors.append(
                f"'{asin}' is not a valid ASIN. "
                "ASINs are 10 characters, start with B or a digit, and are alphanumeric."
            )

    # Check for duplicates
    all_asins = [your_asin.upper()] + [a.upper() for a in competitor_asins]
    if len(all_asins) != len(set(all_asins)):
        errors.append("Duplicate ASINs detected. All ASINs must be unique.")

    return errors
