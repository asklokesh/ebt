"""Confidence score calculation for classifications."""

from typing import Optional

from src.core.constants import (
    CONFIDENCE_HIGH,
    CONFIDENCE_LOW,
    CONFIDENCE_MEDIUM,
    ClassificationCategory,
)
from src.models.classification import AIReasoningResult, RuleValidationResult
from src.models.product import ProductInput
from src.utils.logging import get_logger

logger = get_logger(__name__)


class ConfidenceScorer:
    """
    Calculates confidence scores for classifications.

    Confidence is based on:
    - Completeness of input data
    - Whether rule-based or AI-based classification
    - Consistency between rule and AI results
    - Quality of evidence (citations, reasoning)
    """

    # Weights for different factors
    WEIGHTS = {
        "rule_based": 0.3,
        "data_completeness": 0.25,
        "ai_consistency": 0.25,
        "evidence_quality": 0.2,
    }

    # Required fields for full confidence
    REQUIRED_FIELDS = [
        "product_name",
        "category",
        "nutrition_label_type",
    ]

    # Optional but helpful fields
    HELPFUL_FIELDS = [
        "description",
        "brand",
        "upc",
        "ingredients",
    ]

    def calculate(
        self,
        product: ProductInput,
        rule_result: RuleValidationResult,
        ai_result: Optional[AIReasoningResult] = None,
    ) -> float:
        """
        Calculate confidence score for a classification.

        Args:
            product: Product input
            rule_result: Result from rule-based validation
            ai_result: Result from AI reasoning (if used)

        Returns:
            Confidence score between 0.0 and 1.0
        """
        scores = {
            "rule_based": self._score_rule_based(rule_result),
            "data_completeness": self._score_data_completeness(product),
            "ai_consistency": self._score_ai_consistency(rule_result, ai_result),
            "evidence_quality": self._score_evidence_quality(rule_result, ai_result),
        }

        # Calculate weighted average
        total_weight = sum(self.WEIGHTS.values())
        weighted_sum = sum(
            scores[key] * self.WEIGHTS[key] for key in scores
        )
        confidence = weighted_sum / total_weight

        # Ensure confidence is between 0 and 1
        confidence = max(0.0, min(1.0, confidence))

        logger.info(
            "confidence_calculated",
            product_id=product.product_id,
            confidence=confidence,
            scores=scores,
        )

        return round(confidence, 2)

    def _score_rule_based(self, rule_result: RuleValidationResult) -> float:
        """
        Score based on whether rule-based classification was possible.

        Deterministic rule-based results get high confidence.
        """
        if rule_result.is_deterministic:
            # Clear-cut cases get high confidence
            return 1.0
        else:
            # Ambiguous cases start with medium confidence
            return CONFIDENCE_MEDIUM

    def _score_data_completeness(self, product: ProductInput) -> float:
        """
        Score based on how complete the product data is.

        More complete data = higher confidence.
        """
        # Check required fields
        required_present = sum(
            1 for field in self.REQUIRED_FIELDS
            if getattr(product, field, None) is not None
        )
        required_score = required_present / len(self.REQUIRED_FIELDS)

        # Check helpful fields
        helpful_present = sum(
            1 for field in self.HELPFUL_FIELDS
            if getattr(product, field, None) is not None
        )
        helpful_score = helpful_present / len(self.HELPFUL_FIELDS)

        # Weight required fields more heavily
        return (required_score * 0.7) + (helpful_score * 0.3)

    def _score_ai_consistency(
        self,
        rule_result: RuleValidationResult,
        ai_result: Optional[AIReasoningResult],
    ) -> float:
        """
        Score based on consistency between rule and AI results.

        When both agree, confidence is high.
        """
        if rule_result.is_deterministic:
            # Rule-based was conclusive, no AI needed
            return 1.0

        if ai_result is None:
            # No AI result to compare
            return CONFIDENCE_MEDIUM

        # Check if there are any partial indicators from rule validation
        rule_indicators = rule_result.key_factors

        # If AI result has strong reasoning chain, boost confidence
        if len(ai_result.reasoning_chain) >= 3:
            return CONFIDENCE_HIGH
        elif len(ai_result.reasoning_chain) >= 1:
            return CONFIDENCE_MEDIUM
        else:
            return CONFIDENCE_LOW

    def _score_evidence_quality(
        self,
        rule_result: RuleValidationResult,
        ai_result: Optional[AIReasoningResult],
    ) -> float:
        """
        Score based on quality of evidence supporting the classification.

        More citations and reasoning = higher confidence.
        """
        citations_count = len(rule_result.citations)
        reasoning_count = len(rule_result.reasoning_chain)

        if ai_result:
            citations_count += len(ai_result.citations)
            reasoning_count += len(ai_result.reasoning_chain)

        # Score based on evidence volume
        citation_score = min(1.0, citations_count / 3)  # Max out at 3 citations
        reasoning_score = min(1.0, reasoning_count / 5)  # Max out at 5 reasoning steps

        return (citation_score * 0.4) + (reasoning_score * 0.6)

    def get_confidence_label(self, confidence: float) -> str:
        """
        Get a human-readable confidence label.

        Args:
            confidence: Confidence score (0.0 - 1.0)

        Returns:
            Label string
        """
        if confidence >= CONFIDENCE_HIGH:
            return "High"
        elif confidence >= CONFIDENCE_MEDIUM:
            return "Medium"
        elif confidence >= CONFIDENCE_LOW:
            return "Low"
        else:
            return "Very Low"

    def should_flag_for_review(self, confidence: float) -> bool:
        """
        Determine if a classification should be flagged for review.

        Args:
            confidence: Confidence score

        Returns:
            True if should be flagged
        """
        return confidence < CONFIDENCE_MEDIUM

    def calculate_simple(
        self,
        is_rule_based: bool,
        has_citations: bool,
        data_complete: bool,
    ) -> float:
        """
        Simple confidence calculation for quick estimates.

        Args:
            is_rule_based: Whether determined by rules
            has_citations: Whether citations are present
            data_complete: Whether input data is complete

        Returns:
            Confidence score
        """
        base = CONFIDENCE_MEDIUM

        if is_rule_based:
            base = 1.0
        elif has_citations:
            base += 0.1

        if data_complete:
            base += 0.05

        return min(1.0, base)
