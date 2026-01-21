"""Custom exceptions for the EBT classification system."""

from typing import Any, Optional


class EBTClassificationError(Exception):
    """Base exception for EBT classification errors."""

    def __init__(self, message: str, details: Optional[dict[str, Any]] = None):
        self.message = message
        self.details = details or {}
        super().__init__(self.message)


class ValidationError(EBTClassificationError):
    """Raised when input validation fails."""

    pass


class ClassificationError(EBTClassificationError):
    """Raised when classification fails."""

    pass


class AIReasoningError(EBTClassificationError):
    """Raised when AI reasoning fails."""

    pass


class DatabaseError(EBTClassificationError):
    """Raised when database operations fail."""

    pass


class ExternalAPIError(EBTClassificationError):
    """Raised when external API calls fail."""

    def __init__(
        self,
        message: str,
        api_name: str,
        status_code: Optional[int] = None,
        details: Optional[dict[str, Any]] = None,
    ):
        self.api_name = api_name
        self.status_code = status_code
        super().__init__(message, details)


class RateLimitError(EBTClassificationError):
    """Raised when rate limits are exceeded."""

    def __init__(
        self,
        message: str,
        service: str,
        retry_after: Optional[int] = None,
        details: Optional[dict[str, Any]] = None,
    ):
        self.service = service
        self.retry_after = retry_after
        super().__init__(message, details)


class ChallengeError(EBTClassificationError):
    """Raised when challenge workflow fails."""

    pass


class AuditNotFoundError(EBTClassificationError):
    """Raised when audit record is not found."""

    def __init__(self, audit_id: str):
        self.audit_id = audit_id
        super().__init__(f"Audit record not found: {audit_id}")


class ProductNotFoundError(EBTClassificationError):
    """Raised when product is not found."""

    def __init__(self, product_id: str):
        self.product_id = product_id
        super().__init__(f"Product not found: {product_id}")


class RAGError(EBTClassificationError):
    """Raised when RAG operations fail."""

    pass


class VectorStoreError(RAGError):
    """Raised when vector store operations fail."""

    pass


class EmbeddingError(RAGError):
    """Raised when embedding generation fails."""

    pass
