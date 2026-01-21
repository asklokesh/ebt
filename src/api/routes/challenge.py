"""Challenge endpoint for disputing classifications."""

from fastapi import APIRouter, Depends, HTTPException

from src.api.dependencies import get_challenger
from src.core.exceptions import AuditNotFoundError, ChallengeError
from src.models.audit import ChallengeRequest, ChallengeResponse
from src.services.challenge_handler import ChallengeHandler

router = APIRouter(prefix="/challenge", tags=["challenge"])


@router.post("/{audit_id}", response_model=ChallengeResponse)
async def challenge_classification(
    audit_id: str,
    challenge: ChallengeRequest,
    handler: ChallengeHandler = Depends(get_challenger),
) -> ChallengeResponse:
    """
    Challenge an existing classification.

    Args:
        audit_id: Audit ID of the classification to challenge
        challenge: Challenge request with reason and evidence

    Returns:
        ChallengeResponse with original and new classifications
    """
    try:
        result = await handler.process_challenge(
            audit_id=audit_id,
            challenge=challenge,
        )
        return result

    except AuditNotFoundError:
        raise HTTPException(
            status_code=404,
            detail=f"Audit record not found: {audit_id}",
        )
    except ChallengeError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{audit_id}/history")
async def get_challenge_history(
    audit_id: str,
    handler: ChallengeHandler = Depends(get_challenger),
) -> dict:
    """
    Get challenge history for a product.

    Args:
        audit_id: Original audit ID

    Returns:
        Challenge history
    """
    try:
        from src.data.repositories.audit_repo import AuditRepository

        audit_repo = AuditRepository()
        audit_record = await audit_repo.get_by_audit_id(audit_id)

        if not audit_record:
            raise HTTPException(
                status_code=404,
                detail=f"Audit record not found: {audit_id}",
            )

        product_id = audit_record.classification_result.product_id
        history = await handler.get_challenge_history(product_id)

        return {
            "product_id": product_id,
            "challenges": history,
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
