"""Explanation endpoint for detailed classification reasoning."""

from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException

from src.api.dependencies import get_audit_repository
from src.core.exceptions import AuditNotFoundError
from src.data.repositories.audit_repo import AuditRepository

router = APIRouter(prefix="/explain", tags=["explanation"])


@router.get("/{audit_id}")
async def get_explanation(
    audit_id: str,
    audit_repo: AuditRepository = Depends(get_audit_repository),
) -> Dict[str, Any]:
    """
    Get detailed explanation for a classification.

    Args:
        audit_id: Audit ID of the classification

    Returns:
        Detailed explanation with reasoning and citations
    """
    try:
        audit_record = await audit_repo.get_by_audit_id(audit_id)

        if not audit_record:
            raise HTTPException(
                status_code=404,
                detail=f"Audit record not found: {audit_id}",
            )

        result = audit_record.classification_result

        return {
            "audit_id": audit_id,
            "product": {
                "product_id": result.product_id,
                "product_name": result.product_name,
            },
            "classification": {
                "is_ebt_eligible": result.is_ebt_eligible,
                "confidence_score": result.confidence_score,
                "classification_category": result.classification_category.value,
            },
            "explanation": {
                "reasoning_chain": result.reasoning_chain,
                "key_factors": result.key_factors,
                "regulation_citations": [
                    {
                        "regulation_id": c.regulation_id,
                        "section": c.section,
                        "excerpt": c.excerpt,
                        "relevance_score": c.relevance_score,
                        "source_url": c.source_url,
                    }
                    for c in result.regulation_citations
                ],
            },
            "metadata": {
                "classification_timestamp": result.classification_timestamp.isoformat(),
                "model_version": result.model_version,
                "processing_time_ms": result.processing_time_ms,
                "data_sources_used": result.data_sources_used,
            },
            "original_request": audit_record.request_payload,
            "challenge_info": {
                "was_challenged": audit_record.was_challenged,
                "challenge_reason": audit_record.challenge_reason,
                "challenge_timestamp": (
                    audit_record.challenge_timestamp.isoformat()
                    if audit_record.challenge_timestamp
                    else None
                ),
            },
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
