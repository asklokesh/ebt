"""
Main classification engine that orchestrates rule-based validation
and AI reasoning for EBT eligibility determination.
"""

import asyncio
from datetime import datetime
from typing import Optional
import uuid

from src.core.constants import MODEL_VERSION
from src.core.exceptions import ClassificationError
from src.data.repositories.audit_repo import AuditRepository
from src.data.repositories.classification_repo import ClassificationRepository
from src.data.repositories.product_repo import ProductRepository
from src.models.audit import AuditRecord
from src.models.classification import (
    BulkClassificationResult,
    BulkClassificationSummary,
    ClassificationResult,
)
from src.models.product import ProductInput
from src.services.ai_reasoning_agent import AIReasoningAgent
from src.services.confidence_scorer import ConfidenceScorer
from src.services.rule_validator import RuleValidator
from src.utils.hashing import compute_request_hash
from src.utils.logging import get_logger

logger = get_logger(__name__)


class ClassificationEngine:
    """
    Orchestrates the EBT eligibility classification process.

    Classification Flow:
    1. Check cache for existing classification
    2. Apply rule-based validation for clear-cut cases
    3. If ambiguous, invoke AI reasoning agent
    4. Calculate confidence score
    5. Store result and audit trail
    """

    def __init__(
        self,
        rule_validator: RuleValidator = None,
        ai_agent: AIReasoningAgent = None,
        confidence_scorer: ConfidenceScorer = None,
        product_repo: ProductRepository = None,
        classification_repo: ClassificationRepository = None,
        audit_repo: AuditRepository = None,
    ):
        """
        Initialize the classification engine.

        Args:
            rule_validator: Rule-based validator
            ai_agent: AI reasoning agent
            confidence_scorer: Confidence calculator
            product_repo: Product repository
            classification_repo: Classification repository
            audit_repo: Audit trail repository
        """
        self.rule_validator = rule_validator or RuleValidator()
        self.ai_agent = ai_agent or AIReasoningAgent()
        self.confidence_scorer = confidence_scorer or ConfidenceScorer()
        self.product_repo = product_repo or ProductRepository()
        self.classification_repo = classification_repo or ClassificationRepository()
        self.audit_repo = audit_repo or AuditRepository()

    async def classify(
        self,
        product: ProductInput,
        request_source: str = "API",
        force_reprocess: bool = False,
    ) -> ClassificationResult:
        """
        Classify a product for EBT eligibility.

        Args:
            product: Product input data
            request_source: Origin of request (API, UI, Batch)
            force_reprocess: Skip cache and reprocess

        Returns:
            ClassificationResult with eligibility determination
        """
        start_time = datetime.utcnow()
        audit_id = str(uuid.uuid4())
        request_hash = compute_request_hash(product)

        logger.info(
            "classification_started",
            product_id=product.product_id,
            audit_id=audit_id,
        )

        try:
            # Step 1: Check cache (unless forced reprocess)
            if not force_reprocess:
                cached = await self.classification_repo.get_by_product_id(
                    product.product_id
                )
                if cached:
                    logger.info("cache_hit", product_id=product.product_id)
                    return cached

            # Step 2: Save product to database
            await self.product_repo.save(product)

            # Step 3: Apply rule-based validation
            rule_result = self.rule_validator.validate(product)

            if rule_result.is_deterministic:
                # Clear-cut case - use rule-based result
                logger.info(
                    "rule_based_classification",
                    product_id=product.product_id,
                    category=rule_result.category.value if rule_result.category else None,
                )

                classification = self._build_result(
                    product=product,
                    is_eligible=rule_result.is_eligible,
                    category=rule_result.category,
                    reasoning=rule_result.reasoning_chain,
                    citations=rule_result.citations,
                    key_factors=rule_result.key_factors,
                    confidence=1.0,  # Rule-based = high confidence
                    audit_id=audit_id,
                    request_hash=request_hash,
                    start_time=start_time,
                    data_sources=["Rule-based validator"],
                )
            else:
                # Step 4: Invoke AI reasoning agent for ambiguous cases
                logger.info(
                    "ai_reasoning_required",
                    product_id=product.product_id,
                )

                ai_result = await self.ai_agent.reason(
                    product=product,
                    partial_rule_result=rule_result,
                )

                # Step 5: Calculate confidence score
                confidence = self.confidence_scorer.calculate(
                    product=product,
                    rule_result=rule_result,
                    ai_result=ai_result,
                )

                classification = self._build_result(
                    product=product,
                    is_eligible=ai_result.is_eligible,
                    category=ai_result.category,
                    reasoning=ai_result.reasoning_chain,
                    citations=ai_result.citations,
                    key_factors=ai_result.key_factors,
                    confidence=confidence,
                    audit_id=audit_id,
                    request_hash=request_hash,
                    start_time=start_time,
                    data_sources=ai_result.data_sources_used,
                )

            # Step 6: Store classification and audit trail
            await self.classification_repo.save(classification)
            await self._store_audit(
                audit_id=audit_id,
                product=product,
                result=classification,
                request_source=request_source,
            )

            logger.info(
                "classification_completed",
                product_id=product.product_id,
                is_eligible=classification.is_ebt_eligible,
                confidence=classification.confidence_score,
                processing_time_ms=classification.processing_time_ms,
            )

            return classification

        except Exception as e:
            logger.error(
                "classification_failed",
                product_id=product.product_id,
                error=str(e),
            )
            raise ClassificationError(
                f"Classification failed for product {product.product_id}: {e}"
            )

    async def bulk_classify(
        self,
        products: list[ProductInput],
        max_concurrent: int = 5,
        fail_fast: bool = False,
    ) -> BulkClassificationResult:
        """
        Classify multiple products with concurrency control.

        Args:
            products: List of products to classify
            max_concurrent: Max concurrent classifications
            fail_fast: Stop on first error if True

        Returns:
            BulkClassificationResult with results and summary statistics
        """
        start_time = datetime.utcnow()
        semaphore = asyncio.Semaphore(max_concurrent)
        results = []
        errors = []

        async def classify_with_semaphore(product: ProductInput):
            async with semaphore:
                try:
                    result = await self.classify(product, request_source="Batch")
                    return {"success": True, "result": result}
                except Exception as e:
                    if fail_fast:
                        raise
                    return {
                        "success": False,
                        "product_id": product.product_id,
                        "error": str(e),
                    }

        tasks = [classify_with_semaphore(p) for p in products]
        completed = await asyncio.gather(*tasks, return_exceptions=not fail_fast)

        for item in completed:
            if isinstance(item, Exception):
                errors.append({"error": str(item)})
            elif item["success"]:
                results.append(item["result"])
            else:
                errors.append(item)

        # Calculate summary
        eligible_count = sum(1 for r in results if r.is_ebt_eligible)
        low_confidence_count = sum(1 for r in results if r.confidence_score < 0.8)

        end_time = datetime.utcnow()
        processing_time_ms = int((end_time - start_time).total_seconds() * 1000)

        return BulkClassificationResult(
            total_products=len(products),
            successful=len(results),
            failed=len(errors),
            processing_time_ms=processing_time_ms,
            results=results,
            errors=errors,
            summary=BulkClassificationSummary(
                eligible_count=eligible_count,
                ineligible_count=len(results) - eligible_count,
                low_confidence_count=low_confidence_count,
            ),
        )

    def _build_result(
        self,
        product: ProductInput,
        is_eligible: bool,
        category,
        reasoning: list[str],
        citations: list,
        key_factors: list[str],
        confidence: float,
        audit_id: str,
        request_hash: str,
        start_time: datetime,
        data_sources: list[str],
    ) -> ClassificationResult:
        """Build the classification result object."""
        end_time = datetime.utcnow()
        processing_time_ms = int((end_time - start_time).total_seconds() * 1000)

        return ClassificationResult(
            product_id=product.product_id,
            product_name=product.product_name,
            is_ebt_eligible=is_eligible,
            confidence_score=confidence,
            classification_category=category,
            reasoning_chain=reasoning,
            regulation_citations=citations,
            key_factors=key_factors,
            classification_timestamp=end_time,
            model_version=MODEL_VERSION,
            processing_time_ms=processing_time_ms,
            data_sources_used=data_sources,
            audit_id=audit_id,
            request_hash=request_hash,
        )

    async def _store_audit(
        self,
        audit_id: str,
        product: ProductInput,
        result: ClassificationResult,
        request_source: str,
    ) -> None:
        """Store audit trail record."""
        audit = AuditRecord(
            audit_id=audit_id,
            timestamp=result.classification_timestamp,
            request_payload=product.model_dump(),
            request_source=request_source,
            classification_result=result,
            model_used=self.ai_agent.model_name,
            tokens_consumed=0,
            rag_documents_retrieved=[],
            was_challenged=False,
        )
        await self.audit_repo.save(audit)


# Global engine instance
_engine: ClassificationEngine | None = None


def get_classification_engine() -> ClassificationEngine:
    """Get the global classification engine instance."""
    global _engine
    if _engine is None:
        _engine = ClassificationEngine()
    return _engine
