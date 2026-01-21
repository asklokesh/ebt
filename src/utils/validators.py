"""Input validation helpers."""

import re
from typing import Optional

from src.core.constants import ALCOHOL_THRESHOLD
from src.core.exceptions import ValidationError


def validate_product_id(product_id: str) -> str:
    """
    Validate product ID format.

    Args:
        product_id: Product identifier to validate

    Returns:
        Validated product ID

    Raises:
        ValidationError: If product ID is invalid
    """
    if not product_id or not product_id.strip():
        raise ValidationError("Product ID cannot be empty")

    product_id = product_id.strip()

    if len(product_id) > 100:
        raise ValidationError("Product ID cannot exceed 100 characters")

    return product_id


def validate_product_name(product_name: str) -> str:
    """
    Validate product name.

    Args:
        product_name: Product name to validate

    Returns:
        Validated product name

    Raises:
        ValidationError: If product name is invalid
    """
    if not product_name or not product_name.strip():
        raise ValidationError("Product name cannot be empty")

    product_name = product_name.strip()

    if len(product_name) > 500:
        raise ValidationError("Product name cannot exceed 500 characters")

    return product_name


def validate_upc(upc: Optional[str]) -> Optional[str]:
    """
    Validate UPC (Universal Product Code).

    Args:
        upc: UPC to validate

    Returns:
        Validated UPC or None

    Raises:
        ValidationError: If UPC format is invalid
    """
    if not upc:
        return None

    upc = upc.strip()

    # UPC-A is 12 digits, EAN-13 is 13 digits
    if not re.match(r"^\d{12,14}$", upc):
        raise ValidationError(
            f"Invalid UPC format: {upc}. Expected 12-14 digits."
        )

    return upc


def validate_alcohol_content(alcohol_content: Optional[float]) -> Optional[float]:
    """
    Validate alcohol content value.

    Args:
        alcohol_content: Alcohol content as decimal (0.0 - 1.0)

    Returns:
        Validated alcohol content or None

    Raises:
        ValidationError: If alcohol content is invalid
    """
    if alcohol_content is None:
        return None

    if alcohol_content < 0 or alcohol_content > 1:
        raise ValidationError(
            f"Alcohol content must be between 0.0 and 1.0, got {alcohol_content}"
        )

    return alcohol_content


def is_alcoholic(alcohol_content: Optional[float]) -> bool:
    """
    Check if alcohol content exceeds the threshold.

    Args:
        alcohol_content: Alcohol content as decimal

    Returns:
        True if alcoholic (>0.5% ABV), False otherwise
    """
    if alcohol_content is None:
        return False
    return alcohol_content > ALCOHOL_THRESHOLD


def validate_confidence_score(score: float) -> float:
    """
    Validate confidence score is within valid range.

    Args:
        score: Confidence score to validate

    Returns:
        Validated confidence score

    Raises:
        ValidationError: If score is out of range
    """
    if score < 0.0 or score > 1.0:
        raise ValidationError(
            f"Confidence score must be between 0.0 and 1.0, got {score}"
        )
    return score


def sanitize_text(text: Optional[str], max_length: int = 1000) -> Optional[str]:
    """
    Sanitize text input by stripping whitespace and limiting length.

    Args:
        text: Text to sanitize
        max_length: Maximum allowed length

    Returns:
        Sanitized text or None
    """
    if not text:
        return None

    text = text.strip()

    if len(text) > max_length:
        text = text[:max_length]

    return text if text else None


def validate_pagination(limit: int, offset: int) -> tuple[int, int]:
    """
    Validate pagination parameters.

    Args:
        limit: Maximum number of records
        offset: Number of records to skip

    Returns:
        Tuple of (validated_limit, validated_offset)

    Raises:
        ValidationError: If parameters are invalid
    """
    if limit < 1:
        raise ValidationError("Limit must be at least 1")

    if limit > 1000:
        raise ValidationError("Limit cannot exceed 1000")

    if offset < 0:
        raise ValidationError("Offset cannot be negative")

    return limit, offset
