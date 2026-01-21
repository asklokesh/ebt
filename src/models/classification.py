"""Pydantic models for classification results."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

from src.core.constants import ClassificationCategory
from src.models.regulation import RegulationCitation


class ClassificationResult(BaseModel):
    """Output schema for classification result."""

    product_id: str = Field(..., description="Product identifier")
    product_name: str = Field(..., description="Product name")

    # Classification
    is_ebt_eligible: bool = Field(
        ...,
        description="Whether the product is EBT/SNAP eligible",
    )
    confidence_score: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Confidence score (0.0 - 1.0)",
    )
    classification_category: ClassificationCategory = Field(
        ...,
        description="Specific classification category",
    )

    # Explainability
    reasoning_chain: list[str] = Field(
        ...,
        description="Step-by-step reasoning",
    )
    regulation_citations: list[RegulationCitation] = Field(
        default_factory=list,
        description="Relevant regulation citations",
    )
    key_factors: list[str] = Field(
        default_factory=list,
        description="Factors that influenced the decision",
    )

    # Metadata
    classification_timestamp: datetime = Field(
        ...,
        description="When the classification was made",
    )
    model_version: str = Field(
        ...,
        description="Version of the classification model",
    )
    processing_time_ms: int = Field(
        ...,
        ge=0,
        description="Processing time in milliseconds",
    )
    data_sources_used: list[str] = Field(
        default_factory=list,
        description="Data sources used for classification",
    )

    # Audit
    audit_id: str = Field(
        ...,
        description="UUID for audit trail",
    )
    request_hash: str = Field(
        ...,
        description="Hash of input for deduplication",
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "product_id": "SKU-12345",
                    "product_name": "Monster Energy Drink Original",
                    "is_ebt_eligible": True,
                    "confidence_score": 0.95,
                    "classification_category": "ELIGIBLE_BEVERAGE",
                    "reasoning_chain": [
                        "Product is intended for human consumption (beverage)",
                        "Product has Nutrition Facts label (not Supplement Facts)",
                        "Alcohol content is 0% (below threshold)",
                        "Product is not hot at point of sale",
                        "CONCLUSION: Product is SNAP-eligible as a non-alcoholic beverage",
                    ],
                    "regulation_citations": [
                        {
                            "regulation_id": "7 CFR 271.2",
                            "section": "eligible food",
                            "excerpt": "Any food or food product for home consumption...",
                            "relevance_score": 0.98,
                            "source_url": "https://www.ecfr.gov/current/title-7/section-271.2",
                        }
                    ],
                    "key_factors": [
                        "Has Nutrition Facts label",
                        "Non-alcoholic beverage",
                        "Cold/room temperature product",
                    ],
                    "classification_timestamp": "2026-01-21T15:30:00Z",
                    "model_version": "1.0.0",
                    "processing_time_ms": 1250,
                    "data_sources_used": ["USDA FoodData Central", "SNAP Guidelines Vector Store"],
                    "audit_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
                    "request_hash": "sha256:abc123...",
                }
            ]
        }
    }


class BulkClassificationSummary(BaseModel):
    """Summary statistics for bulk classification."""

    eligible_count: int = Field(..., ge=0)
    ineligible_count: int = Field(..., ge=0)
    low_confidence_count: int = Field(..., ge=0)


class BulkClassificationResult(BaseModel):
    """Result of bulk classification operation."""

    total_products: int = Field(..., ge=0)
    successful: int = Field(..., ge=0)
    failed: int = Field(..., ge=0)
    processing_time_ms: int = Field(..., ge=0)
    results: list[ClassificationResult] = Field(default_factory=list)
    errors: list[dict] = Field(default_factory=list)
    summary: BulkClassificationSummary


class RuleValidationResult(BaseModel):
    """Result of rule-based validation."""

    is_deterministic: bool = Field(
        ...,
        description="True if rules can definitively classify",
    )
    is_eligible: Optional[bool] = Field(
        default=None,
        description="Eligibility determination (if deterministic)",
    )
    category: Optional[ClassificationCategory] = Field(
        default=None,
        description="Classification category (if deterministic)",
    )
    reasoning_chain: list[str] = Field(
        default_factory=list,
        description="Reasoning steps applied",
    )
    citations: list[RegulationCitation] = Field(
        default_factory=list,
        description="Relevant citations",
    )
    key_factors: list[str] = Field(
        default_factory=list,
        description="Key factors identified",
    )
    ambiguity_reason: Optional[str] = Field(
        default=None,
        description="Reason for ambiguity (if not deterministic)",
    )


class AIReasoningResult(BaseModel):
    """Result from AI reasoning agent."""

    is_eligible: bool
    category: ClassificationCategory
    reasoning_chain: list[str]
    citations: list[RegulationCitation] = Field(default_factory=list)
    key_factors: list[str]
    data_sources_used: list[str]
