"""Challenge workflow handler for disputing classifications."""

from datetime import datetime
from typing import Any, Dict
import uuid

from src.core.exceptions import AuditNotFoundError, ChallengeError
from src.data.repositories.audit_repo import AuditRepository
from src.models.audit import ChallengeRequest, ChallengeResponse
from src.models.classification import ClassificationResult
from src.models.product import ProductInput
from src.services.classification_engine import ClassificationEngine, get_classification_engine
from src.utils.logging import get_logger

logger = get_logger(__name__)


class ChallengeHandler:
    """
    Handles challenge workflow for disputing classifications.

    When a user challenges a classification, this handler:
    1. Retrieves the original classification
    2. Applies any additional evidence from the challenge
    3. Re-runs the classification with updated information
    4. Updates the audit trail with challenge details
    """

    def __init__(
        self,
        audit_repo: AuditRepository = None,
        engine: ClassificationEngine = None,
    ):
        """
        Initialize the challenge handler.

        Args:
            audit_repo: Audit repository
            engine: Classification engine
        """
        self.audit_repo = audit_repo or AuditRepository()
        self.engine = engine or get_classification_engine()

    async def process_challenge(
        self,
        audit_id: str,
        challenge: ChallengeRequest,
    ) -> ChallengeResponse:
        """
        Process a challenge to an existing classification.

        Args:
            audit_id: Audit ID of the classification to challenge
            challenge: Challenge request with reason and evidence

        Returns:
            ChallengeResponse with original and new classifications
        """
        logger.info(
            "challenge_started",
            audit_id=audit_id,
            reason=challenge.challenge_reason[:100],
        )

        try:
            # Step 1: Retrieve the original audit record
            original_audit = await self.audit_repo.get_by_audit_id(audit_id)

            if not original_audit:
                raise AuditNotFoundError(audit_id)

            # Step 2: Extract original product data
            original_product_data = original_audit.request_payload

            # Step 3: Apply additional evidence if provided
            updated_product_data = self._apply_evidence(
                original_product_data,
                challenge.additional_evidence,
            )

            # Step 4: Create updated product input
            updated_product = ProductInput(**updated_product_data)

            # Step 5: Re-classify with force reprocess
            new_classification = await self.engine.classify(
                product=updated_product,
                request_source="Challenge",
                force_reprocess=True,
            )

            # Step 6: Update audit record with challenge details
            await self.audit_repo.update_challenge(
                audit_id=audit_id,
                challenge_reason=challenge.challenge_reason,
                challenge_result=new_classification,
            )

            # Step 7: Determine if classification changed
            original_result = original_audit.classification_result
            classification_changed = (
                original_result.is_ebt_eligible != new_classification.is_ebt_eligible
                or original_result.classification_category
                != new_classification.classification_category
            )

            # Step 8: Build reasoning for change
            reasoning_for_change = self._build_change_reasoning(
                original_result,
                new_classification,
                challenge,
                classification_changed,
            )

            logger.info(
                "challenge_completed",
                audit_id=audit_id,
                classification_changed=classification_changed,
                original_eligible=original_result.is_ebt_eligible,
                new_eligible=new_classification.is_ebt_eligible,
            )

            return ChallengeResponse(
                original_audit_id=audit_id,
                challenge_audit_id=new_classification.audit_id,
                original_classification={
                    "is_ebt_eligible": original_result.is_ebt_eligible,
                    "classification_category": original_result.classification_category.value,
                    "confidence_score": original_result.confidence_score,
                },
                new_classification=new_classification,
                classification_changed=classification_changed,
                reasoning_for_change=reasoning_for_change,
            )

        except AuditNotFoundError:
            raise
        except Exception as e:
            logger.error(
                "challenge_failed",
                audit_id=audit_id,
                error=str(e),
            )
            raise ChallengeError(f"Challenge processing failed: {e}")

    def _apply_evidence(
        self,
        original_data: Dict[str, Any],
        additional_evidence: Dict[str, Any] | None,
    ) -> Dict[str, Any]:
        """
        Apply additional evidence to the original product data.

        Args:
            original_data: Original product data
            additional_evidence: Additional evidence from challenge

        Returns:
            Updated product data
        """
        if not additional_evidence:
            return original_data

        updated_data = original_data.copy()

        # Map evidence fields to product fields
        evidence_mapping = {
            "new_nutrition_label_type": "nutrition_label_type",
            "updated_ingredients": "ingredients",
            "new_category": "category",
            "is_hot_at_sale": "is_hot_at_sale",
            "is_for_onsite_consumption": "is_for_onsite_consumption",
            "alcohol_content": "alcohol_content",
            "contains_tobacco": "contains_tobacco",
            "contains_cbd_cannabis": "contains_cbd_cannabis",
            "is_live_animal": "is_live_animal",
            "new_description": "description",
        }

        for evidence_key, product_key in evidence_mapping.items():
            if evidence_key in additional_evidence:
                updated_data[product_key] = additional_evidence[evidence_key]

        return updated_data

    def _build_change_reasoning(
        self,
        original: ClassificationResult,
        new: ClassificationResult,
        challenge: ChallengeRequest,
        changed: bool,
    ) -> list[str]:
        """
        Build reasoning explaining why classification did or didn't change.

        Args:
            original: Original classification
            new: New classification after challenge
            challenge: The challenge request
            changed: Whether classification changed

        Returns:
            List of reasoning steps
        """
        reasoning = []

        # Original classification summary
        reasoning.append(
            f"Original classification: "
            f"{'ELIGIBLE' if original.is_ebt_eligible else 'INELIGIBLE'} "
            f"({original.classification_category.value})"
        )

        # Challenge reason
        reasoning.append(f"Challenge reason: {challenge.challenge_reason}")

        # Evidence applied
        if challenge.additional_evidence:
            evidence_str = ", ".join(
                f"{k}={v}" for k, v in challenge.additional_evidence.items()
            )
            reasoning.append(f"Additional evidence applied: {evidence_str}")

        # Result
        if changed:
            reasoning.append(
                f"New classification: "
                f"{'ELIGIBLE' if new.is_ebt_eligible else 'INELIGIBLE'} "
                f"({new.classification_category.value})"
            )
            reasoning.append("Classification CHANGED based on new evidence")
        else:
            reasoning.append("Classification UNCHANGED - original determination stands")
            reasoning.append(
                "The additional evidence did not affect eligibility determination"
            )

        return reasoning

    async def get_challenge_history(
        self,
        product_id: str,
    ) -> list[Dict[str, Any]]:
        """
        Get challenge history for a product.

        Args:
            product_id: Product identifier

        Returns:
            List of challenge records
        """
        from src.models.audit import AuditTrailQuery

        query = AuditTrailQuery(
            product_id=product_id,
            was_challenged=True,
            limit=100,
        )

        records = await self.audit_repo.query(query)

        return [
            {
                "audit_id": r.audit_id,
                "timestamp": r.timestamp.isoformat(),
                "challenge_reason": r.challenge_reason,
                "original_eligible": r.classification_result.is_ebt_eligible,
                "challenge_eligible": (
                    r.challenge_result.is_ebt_eligible
                    if r.challenge_result
                    else None
                ),
                "changed": (
                    r.classification_result.is_ebt_eligible
                    != r.challenge_result.is_ebt_eligible
                    if r.challenge_result
                    else False
                ),
            }
            for r in records
        ]


# Global handler instance
_handler: ChallengeHandler | None = None


def get_challenge_handler() -> ChallengeHandler:
    """Get the global challenge handler instance."""
    global _handler
    if _handler is None:
        _handler = ChallengeHandler()
    return _handler
