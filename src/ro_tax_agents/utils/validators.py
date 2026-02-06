"""Validators for Romanian tax identifiers."""

import re


def validate_cnp(cnp: str) -> bool:
    """Validate Romanian CNP (Cod Numeric Personal).

    CNP has 13 digits with a specific structure and checksum.

    Args:
        cnp: The CNP string to validate

    Returns:
        True if valid, False otherwise
    """
    if not cnp or not re.match(r"^\d{13}$", cnp):
        return False

    # Control key for checksum
    control_key = [2, 7, 9, 1, 4, 6, 3, 5, 8, 2, 7, 9]

    # Calculate checksum
    checksum = sum(int(cnp[i]) * control_key[i] for i in range(12))
    remainder = checksum % 11

    # Check digit is remainder, or 1 if remainder is 10
    expected_check = remainder if remainder < 10 else 1

    return int(cnp[12]) == expected_check


def validate_cui(cui: str) -> bool:
    """Validate Romanian CUI (Cod Unic de Identificare).

    CUI can have 2-10 digits with an optional "RO" prefix for VAT.

    Args:
        cui: The CUI string to validate (with or without RO prefix)

    Returns:
        True if valid, False otherwise
    """
    # Remove RO prefix if present
    cui_clean = cui.upper().replace("RO", "").strip()

    # Must be 2-10 digits
    if not re.match(r"^\d{2,10}$", cui_clean):
        return False

    # Pad with leading zeros to 10 digits for checksum calculation
    cui_padded = cui_clean.zfill(10)

    # Control key for checksum
    control_key = [7, 5, 3, 2, 1, 7, 5, 3, 2]

    # Calculate checksum (excluding last digit)
    checksum = sum(int(cui_padded[i]) * control_key[i] for i in range(9))
    checksum = (checksum * 10) % 11

    # If result is 10, check digit is 0
    expected_check = checksum if checksum < 10 else 0

    return int(cui_padded[9]) == expected_check
