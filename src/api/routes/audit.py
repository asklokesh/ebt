"""Audit trail endpoint."""

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query

from src.api.dependencies import get_audit_repository
from src.data.repositories.audit_repo import AuditRepository
from src.models.audit import AuditTrailQuery

router = APIRouter(prefix="/audit-trail", tags=["audit"])


@router.get("")
@router.get("/")
async def get_audit_trail(
    start_date: Optional[datetime] = Query(None, description="Filter by start date"),
    end_date: Optional[datetime] = Query(None, description="Filter by end date"),
    is_ebt_eligible: Optional[bool] = Query(None, description="Filter by eligibility"),
    classification_category: Optional[str] = Query(
        None, description="Filter by category"
    ),
    was_challenged: Optional[bool] = Query(None, description="Filter by challenge status"),
    product_id: Optional[str] = Query(None, description="Filter by product ID"),
    limit: int = Query(100, ge=1, le=1000, description="Max records to return"),
    offset: int = Query(0, ge=0, description="Pagination offset"),
    audit_repo: AuditRepository = Depends(get_audit_repository),
) -> dict:
    """
    Query audit trail records with filters.

    Returns:
        Paginated audit trail records
    """
    try:
        query = AuditTrailQuery(
            start_date=start_date,
            end_date=end_date,
            is_ebt_eligible=is_ebt_eligible,
            classification_category=classification_category,
            was_challenged=was_challenged,
            product_id=product_id,
            limit=limit,
            offset=offset,
        )

        # Get summaries instead of full records for better performance
        summaries = await audit_repo.get_summaries(query)
        total = await audit_repo.count(query)

        return {
            "total_records": total,
            "returned_records": len(summaries),
            "limit": limit,
            "offset": offset,
            "records": [
                {
                    "audit_id": s.audit_id,
                    "timestamp": s.timestamp.isoformat(),
                    "product_id": s.product_id,
                    "product_name": s.product_name,
                    "is_ebt_eligible": s.is_ebt_eligible,
                    "classification_category": s.classification_category,
                    "confidence_score": s.confidence_score,
                    "model_used": s.model_used,
                    "was_challenged": s.was_challenged,
                }
                for s in summaries
            ],
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats")
async def get_audit_stats(
    audit_repo: AuditRepository = Depends(get_audit_repository),
) -> dict:
    """
    Get audit trail statistics.

    Returns:
        Statistics summary
    """
    try:
        # Count all records
        total_query = AuditTrailQuery(limit=1)
        total = await audit_repo.count(total_query)

        # Count eligible
        eligible_query = AuditTrailQuery(is_ebt_eligible=True, limit=1)
        eligible = await audit_repo.count(eligible_query)

        # Count challenged
        challenged_query = AuditTrailQuery(was_challenged=True, limit=1)
        challenged = await audit_repo.count(challenged_query)

        return {
            "total_classifications": total,
            "eligible_count": eligible,
            "ineligible_count": total - eligible,
            "challenged_count": challenged,
            "eligibility_rate": eligible / total if total > 0 else 0,
            "challenge_rate": challenged / total if total > 0 else 0,
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{audit_id}")
async def get_audit_record(
    audit_id: str,
    audit_repo: AuditRepository = Depends(get_audit_repository),
) -> dict:
    """
    Get a specific audit record.

    Args:
        audit_id: Audit ID

    Returns:
        Full audit record
    """
    try:
        record = await audit_repo.get_by_audit_id(audit_id)

        if not record:
            raise HTTPException(
                status_code=404,
                detail=f"Audit record not found: {audit_id}",
            )

        return {
            "audit_id": record.audit_id,
            "timestamp": record.timestamp.isoformat(),
            "request_source": record.request_source,
            "request_payload": record.request_payload,
            "classification_result": {
                "product_id": record.classification_result.product_id,
                "product_name": record.classification_result.product_name,
                "is_ebt_eligible": record.classification_result.is_ebt_eligible,
                "confidence_score": record.classification_result.confidence_score,
                "classification_category": record.classification_result.classification_category.value,
                "reasoning_chain": record.classification_result.reasoning_chain,
                "key_factors": record.classification_result.key_factors,
            },
            "model_used": record.model_used,
            "tokens_consumed": record.tokens_consumed,
            "rag_documents_retrieved": record.rag_documents_retrieved,
            "was_challenged": record.was_challenged,
            "challenge_reason": record.challenge_reason,
            "challenge_timestamp": (
                record.challenge_timestamp.isoformat()
                if record.challenge_timestamp
                else None
            ),
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
