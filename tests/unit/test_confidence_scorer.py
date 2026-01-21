"""Unit tests for the confidence scorer."""

import pytest
from src.services.confidence_scorer import ConfidenceScorer
from src.models.product import ProductInput
from src.models.classification import RuleValidationResult, AIReasoningResult
from src.core.constants import ClassificationCategory


class TestConfidenceScorer:
    """Test suite for ConfidenceScorer."""

    @pytest.fixture
    def scorer(self) -> ConfidenceScorer:
        """Create a confidence scorer instance."""
        return ConfidenceScorer()

    def test_high_confidence_deterministic_rule(self, scorer: ConfidenceScorer):
        """Test that deterministic rule-based results get high confidence."""
        product = ProductInput(
            product_id="TEST-001",
            product_name="Fresh Apples",
            category="Produce",
            nutrition_label_type="nutrition_facts",
        )
        rule_result = RuleValidationResult(
            is_deterministic=True,
            is_eligible=True,
            category=ClassificationCategory.ELIGIBLE_STAPLE_FOOD,
            reasoning_chain=[
                "Product is fresh produce",
                "Has Nutrition Facts label",
                "No disqualifying factors",
                "Eligible under SNAP",
            ],
            citations=[],
            key_factors=["Produce category", "Nutrition Facts label"],
        )

        score = scorer.calculate(
            product=product,
            rule_result=rule_result,
            ai_result=None,
        )

        assert score >= 0.8
        assert score <= 1.0

    def test_high_confidence_alcohol_ineligible(self, scorer: ConfidenceScorer):
        """Test that alcohol ineligibility with complete data gets high confidence."""
        product = ProductInput(
            product_id="TEST-002",
            product_name="Budweiser Beer",
            category="Beverages",
            alcohol_content=0.05,
            nutrition_label_type="nutrition_facts",
        )
        rule_result = RuleValidationResult(
            is_deterministic=True,
            is_eligible=False,
            category=ClassificationCategory.INELIGIBLE_ALCOHOL,
            reasoning_chain=[
                "Product contains 5.0% alcohol",
                "Alcoholic beverages are explicitly excluded from SNAP eligibility",
            ],
            citations=[],
            key_factors=["Contains alcohol above 0.5% ABV"],
        )

        score = scorer.calculate(
            product=product,
            rule_result=rule_result,
            ai_result=None,
        )

        # With complete required fields and deterministic result, should be >= 0.7
        assert score >= 0.7

    def test_medium_confidence_ai_with_reasoning(self, scorer: ConfidenceScorer):
        """Test that AI results with reasoning get medium-high confidence."""
        product = ProductInput(
            product_id="TEST-003",
            product_name="Protein Powder",
            category="Health",
        )
        rule_result = RuleValidationResult(
            is_deterministic=False,
            reasoning_chain=["Initial validation passed", "Requires AI reasoning"],
            citations=[],
            key_factors=[],
            ambiguity_reason="Product does not match clear-cut rules",
        )
        ai_result = AIReasoningResult(
            is_eligible=False,
            category=ClassificationCategory.INELIGIBLE_SUPPLEMENT,
            reasoning_chain=[
                "Product is marketed as a dietary supplement",
                "Likely has supplement facts label",
                "Supplements are not eligible under SNAP",
            ],
            citations=[],
            key_factors=["supplement", "dietary", "health product"],
            data_sources_used=["SNAP Guidelines"],
        )

        score = scorer.calculate(
            product=product,
            rule_result=rule_result,
            ai_result=ai_result,
        )

        assert score >= 0.5
        assert score <= 0.95

    def test_lower_confidence_minimal_reasoning(self, scorer: ConfidenceScorer):
        """Test that minimal reasoning gets lower confidence."""
        product = ProductInput(
            product_id="TEST-004",
            product_name="Mystery Food Item",
        )
        rule_result = RuleValidationResult(
            is_deterministic=False,
            reasoning_chain=["Requires AI reasoning"],
            citations=[],
            key_factors=[],
            ambiguity_reason="Product does not match clear-cut rules",
        )
        ai_result = AIReasoningResult(
            is_eligible=True,
            category=ClassificationCategory.ELIGIBLE_STAPLE_FOOD,
            reasoning_chain=["Appears eligible"],
            citations=[],
            key_factors=["unknown"],
            data_sources_used=[],
        )

        score = scorer.calculate(
            product=product,
            rule_result=rule_result,
            ai_result=ai_result,
        )

        # Should be lower than detailed reasoning
        assert score < 0.85

    def test_confidence_with_complete_product_info(self, scorer: ConfidenceScorer):
        """Test that complete product info increases confidence."""
        complete_product = ProductInput(
            product_id="TEST-007",
            product_name="Organic Whole Milk",
            category="Dairy",
            brand="Horizon",
            upc="049000006347",
            description="100% organic whole milk",
            nutrition_label_type="nutrition_facts",
        )
        minimal_product = ProductInput(
            product_id="TEST-008",
            product_name="Milk",
        )
        rule_result_complete = RuleValidationResult(
            is_deterministic=True,
            is_eligible=True,
            category=ClassificationCategory.ELIGIBLE_STAPLE_FOOD,
            reasoning_chain=["Dairy product is eligible"],
            citations=[],
            key_factors=["Dairy category"],
        )
        rule_result_minimal = RuleValidationResult(
            is_deterministic=False,
            reasoning_chain=["Requires AI reasoning"],
            citations=[],
            key_factors=[],
            ambiguity_reason="Insufficient data",
        )

        score_complete = scorer.calculate(
            product=complete_product,
            rule_result=rule_result_complete,
            ai_result=None,
        )
        score_minimal = scorer.calculate(
            product=minimal_product,
            rule_result=rule_result_minimal,
            ai_result=None,
        )

        assert score_complete > score_minimal

    def test_confidence_bounds(self, scorer: ConfidenceScorer):
        """Test that confidence is always between 0 and 1."""
        product = ProductInput(
            product_id="TEST-009",
            product_name="Test Product",
        )
        rule_result = RuleValidationResult(
            is_deterministic=False,
            reasoning_chain=[],
            citations=[],
            key_factors=[],
            ambiguity_reason="Unknown",
        )

        score = scorer.calculate(
            product=product,
            rule_result=rule_result,
            ai_result=None,
        )

        assert score >= 0.0
        assert score <= 1.0

    def test_tobacco_high_confidence(self, scorer: ConfidenceScorer):
        """Test that tobacco products get reasonable confidence ineligible."""
        product = ProductInput(
            product_id="TEST-010",
            product_name="Marlboro Cigarettes",
            category="Tobacco",
            contains_tobacco=True,
        )
        rule_result = RuleValidationResult(
            is_deterministic=True,
            is_eligible=False,
            category=ClassificationCategory.INELIGIBLE_TOBACCO,
            reasoning_chain=[
                "Product contains tobacco or nicotine",
                "Tobacco products are explicitly excluded from SNAP eligibility",
            ],
            citations=[],
            key_factors=["Contains tobacco/nicotine"],
        )

        score = scorer.calculate(
            product=product,
            rule_result=rule_result,
            ai_result=None,
        )

        # Deterministic result should give reasonable confidence
        assert score >= 0.7

    def test_hot_food_high_confidence(self, scorer: ConfidenceScorer):
        """Test that hot food gets reasonable confidence ineligible."""
        product = ProductInput(
            product_id="TEST-011",
            product_name="Hot Pizza",
            category="Prepared Foods",
            is_hot_at_sale=True,
        )
        rule_result = RuleValidationResult(
            is_deterministic=True,
            is_eligible=False,
            category=ClassificationCategory.INELIGIBLE_HOT_FOOD,
            reasoning_chain=[
                "Product is hot at point of sale",
                "Hot foods ready for immediate consumption are not eligible",
            ],
            citations=[],
            key_factors=["Hot at point of sale"],
        )

        score = scorer.calculate(
            product=product,
            rule_result=rule_result,
            ai_result=None,
        )

        # Deterministic result should give reasonable confidence
        assert score >= 0.7

    def test_ai_reasoning_chain_affects_confidence(self, scorer: ConfidenceScorer):
        """Test that longer reasoning chains can affect confidence."""
        product = ProductInput(
            product_id="TEST-012",
            product_name="Ambiguous Product",
        )
        rule_result = RuleValidationResult(
            is_deterministic=False,
            reasoning_chain=["Requires AI reasoning"],
            citations=[],
            key_factors=[],
            ambiguity_reason="Ambiguous product",
        )

        # Detailed AI reasoning
        detailed_ai_result = AIReasoningResult(
            is_eligible=True,
            category=ClassificationCategory.ELIGIBLE_STAPLE_FOOD,
            reasoning_chain=[
                "Product name suggests food item",
                "No indicators of alcohol content",
                "No indicators of tobacco",
                "Not sold hot",
                "Appears to be a staple food product",
            ],
            citations=[],
            key_factors=["food", "staple", "no exclusions"],
            data_sources_used=["SNAP Guidelines"],
        )

        # Brief AI reasoning
        brief_ai_result = AIReasoningResult(
            is_eligible=True,
            category=ClassificationCategory.ELIGIBLE_STAPLE_FOOD,
            reasoning_chain=["Appears eligible"],
            citations=[],
            key_factors=["unknown"],
            data_sources_used=[],
        )

        score_detailed = scorer.calculate(
            product=product,
            rule_result=rule_result,
            ai_result=detailed_ai_result,
        )
        score_brief = scorer.calculate(
            product=product,
            rule_result=rule_result,
            ai_result=brief_ai_result,
        )

        # Detailed reasoning should generally produce equal or higher confidence
        assert score_detailed >= score_brief

    def test_get_confidence_label_high(self, scorer: ConfidenceScorer):
        """Test confidence label for high score."""
        label = scorer.get_confidence_label(0.95)
        assert label == "High"

    def test_get_confidence_label_medium(self, scorer: ConfidenceScorer):
        """Test confidence label for medium score."""
        label = scorer.get_confidence_label(0.75)
        assert label == "Medium"

    def test_get_confidence_label_low(self, scorer: ConfidenceScorer):
        """Test confidence label for low score."""
        label = scorer.get_confidence_label(0.55)
        assert label == "Low"

    def test_get_confidence_label_very_low(self, scorer: ConfidenceScorer):
        """Test confidence label for very low score."""
        label = scorer.get_confidence_label(0.3)
        assert label == "Very Low"

    def test_should_flag_for_review_true(self, scorer: ConfidenceScorer):
        """Test flag for review returns true for low confidence."""
        assert scorer.should_flag_for_review(0.5) is True

    def test_should_flag_for_review_false(self, scorer: ConfidenceScorer):
        """Test flag for review returns false for high confidence."""
        assert scorer.should_flag_for_review(0.9) is False

    def test_calculate_simple_rule_based(self, scorer: ConfidenceScorer):
        """Test simple calculation for rule-based."""
        score = scorer.calculate_simple(
            is_rule_based=True,
            has_citations=True,
            data_complete=True,
        )
        assert score == 1.0

    def test_calculate_simple_not_rule_based(self, scorer: ConfidenceScorer):
        """Test simple calculation for non-rule-based."""
        score = scorer.calculate_simple(
            is_rule_based=False,
            has_citations=True,
            data_complete=True,
        )
        assert score >= 0.7
        assert score < 1.0
