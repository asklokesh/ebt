"""Request hashing utilities for deduplication."""

import hashlib
import json
from typing import Any, Union

from pydantic import BaseModel


def compute_request_hash(data: Union[BaseModel, dict[str, Any]]) -> str:
    """
    Compute a SHA-256 hash of a request for deduplication.

    Args:
        data: Pydantic model or dictionary to hash

    Returns:
        SHA-256 hash string prefixed with 'sha256:'
    """
    if isinstance(data, BaseModel):
        # Convert Pydantic model to dict, excluding None values
        data_dict = data.model_dump(exclude_none=True)
    else:
        data_dict = {k: v for k, v in data.items() if v is not None}

    # Sort keys for consistent hashing
    json_str = json.dumps(data_dict, sort_keys=True, default=str)

    # Compute SHA-256 hash
    hash_bytes = hashlib.sha256(json_str.encode("utf-8")).hexdigest()

    return f"sha256:{hash_bytes}"


def compute_content_hash(content: str) -> str:
    """
    Compute a SHA-256 hash of text content.

    Args:
        content: Text content to hash

    Returns:
        SHA-256 hash string
    """
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


def verify_hash(data: Union[BaseModel, dict[str, Any]], expected_hash: str) -> bool:
    """
    Verify that data matches an expected hash.

    Args:
        data: Data to verify
        expected_hash: Expected hash value

    Returns:
        True if hash matches, False otherwise
    """
    computed = compute_request_hash(data)
    return computed == expected_hash
