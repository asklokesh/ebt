"""Pydantic models for audit trail."""

from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field

from src.models.classification import ClassificationResult


class AuditRecord(BaseModel):
    """Complete audit record for compliance."""

    audit_id: str = Field(..., description="UUID for audit trail")
    timestamp: datetime = Field(..., description="When the record was created")

    # Request
    request_payload: dict[str, Any] = Field(
        ...,
        description="Full input request",
    )
    request_source: str = Field(
        ...,
        description="Origin of request (API, UI, Batch)",
    )

    # Classification
    classification_result: ClassificationResult = Field(
        ...,
        description="The classification result",
    )

    # Processing
    model_used: str = Field(
        ...,
        description="Model used for classification",
    )
    tokens_consumed: int = Field(
        default=0,
        ge=0,
        description="Tokens consumed by AI model",
    )
    rag_documents_retrieved: list[str] = Field(
        default_factory=list,
        description="Documents retrieved from vector store",
    )

    # Challenge (if disputed)
    was_challenged: bool = Field(
        default=False,
        description="Whether this classification was challenged",
    )
    challenge_reason: Optional[str] = Field(
        default=None,
        description="Reason for challenge",
    )
    challenge_result: Optional[ClassificationResult] = Field(
        default=None,
        description="Result of challenge re-evaluation",
    )
    challenge_timestamp: Optional[datetime] = Field(
        default=None,
        description="When the challenge was processed",
    )


class AuditTrailQuery(BaseModel):
    """Query parameters for audit trail search."""

    start_date: Optional[datetime] = Field(
        default=None,
        description="Filter by start date",
    )
    end_date: Optional[datetime] = Field(
        default=None,
        description="Filter by end date",
    )
    is_ebt_eligible: Optional[bool] = Field(
        default=None,
        description="Filter by eligibility",
    )
    classification_category: Optional[str] = Field(
        default=None,
        description="Filter by category",
    )
    was_challenged: Optional[bool] = Field(
        default=None,
        description="Filter by challenge status",
    )
    product_id: Optional[str] = Field(
        default=None,
        description="Filter by product ID",
    )
    limit: int = Field(
        default=100,
        ge=1,
        le=1000,
        description="Maximum records to return",
    )
    offset: int = Field(
        default=0,
        ge=0,
        description="Pagination offset",
    )


class AuditTrailResponse(BaseModel):
    """Response for audit trail query."""

    total_records: int = Field(..., ge=0)
    returned_records: int = Field(..., ge=0)
    records: list[AuditRecord]


class AuditSummary(BaseModel):
    """Summary record for audit trail listing."""

    audit_id: str
    timestamp: datetime
    product_id: str
    product_name: str
    is_ebt_eligible: bool
    classification_category: str
    confidence_score: float
    model_used: str
    was_challenged: bool


class ChallengeRequest(BaseModel):
    """Request to challenge a classification."""

    challenge_reason: str = Field(
        ...,
        min_length=10,
        max_length=1000,
        description="Reason for challenging the classification",
    )
    additional_evidence: Optional[dict[str, Any]] = Field(
        default=None,
        description="Additional evidence supporting the challenge",
    )


class ChallengeResponse(BaseModel):
    """Response to a challenge request."""

    original_audit_id: str
    challenge_audit_id: str
    original_classification: dict[str, Any]
    new_classification: ClassificationResult
    classification_changed: bool
    reasoning_for_change: list[str]
