"""Pydantic models for regulation citations."""

from pydantic import BaseModel, Field


class RegulationCitation(BaseModel):
    """Citation to a specific SNAP regulation."""

    regulation_id: str = Field(
        ...,
        description="Regulation identifier (e.g., '7 CFR 271.2')",
        examples=["7 CFR 271.2"],
    )
    section: str = Field(
        ...,
        description="Section within the regulation",
        examples=["eligible food"],
    )
    excerpt: str = Field(
        ...,
        description="Relevant excerpt from the regulation",
    )
    relevance_score: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="How relevant this citation is to the decision",
    )
    source_url: str = Field(
        ...,
        description="Link to official source",
        examples=["https://www.ecfr.gov/current/title-7/section-271.2"],
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "regulation_id": "7 CFR 271.2",
                    "section": "eligible food",
                    "excerpt": "Any food or food product for home consumption except alcoholic beverages, tobacco, and hot food...",
                    "relevance_score": 0.98,
                    "source_url": "https://www.ecfr.gov/current/title-7/section-271.2",
                }
            ]
        }
    }


class RegulationDocument(BaseModel):
    """A regulation document for the vector store."""

    document_id: str = Field(..., description="Unique document identifier")
    title: str = Field(..., description="Document title")
    content: str = Field(..., description="Full document content")
    source: str = Field(..., description="Source of the document")
    source_url: str = Field(..., description="URL to the source")
    regulation_type: str = Field(
        ...,
        description="Type of regulation (cfr, fns_policy, guidance)",
    )
