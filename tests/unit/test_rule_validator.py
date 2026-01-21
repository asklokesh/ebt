"""Unit tests for the rule validator."""

import pytest
from src.services.rule_validator import RuleValidator
from src.models.product import ProductInput
from src.core.constants import ClassificationCategory


class TestRuleValidator:
    """Test suite for RuleValidator."""

    @pytest.fixture
    def validator(self) -> RuleValidator:
        """Create a rule validator instance."""
        return RuleValidator()

    def test_alcohol_ineligible(self, validator: RuleValidator):
        """Test that products with alcohol > 0.5% ABV are ineligible."""
        product = ProductInput(
            product_id="TEST-ALC-001",
            product_name="Budweiser Beer",
            category="Beverages",
            alcohol_content=0.05,  # 5% ABV
        )
        result = validator.validate(product)

        assert result.is_deterministic is True
        assert result.is_eligible is False
        assert result.category == ClassificationCategory.INELIGIBLE_ALCOHOL
        # Check reasoning chain contains alcohol reference
        reasoning_text = " ".join(result.reasoning_chain).lower()
        assert "alcohol" in reasoning_text

    def test_alcohol_below_threshold_eligible(self, validator: RuleValidator):
        """Test that products with alcohol <= 0.5% ABV can be eligible."""
        product = ProductInput(
            product_id="TEST-ALC-002",
            product_name="Non-Alcoholic Beer",
            category="Beverages",
            alcohol_content=0.004,  # 0.4% ABV - below threshold
            nutrition_label_type="nutrition_facts",
        )
        result = validator.validate(product)

        # Should not be flagged as alcohol ineligible
        assert result.category != ClassificationCategory.INELIGIBLE_ALCOHOL

    def test_tobacco_ineligible(self, validator: RuleValidator):
        """Test that tobacco products are ineligible."""
        product = ProductInput(
            product_id="TEST-TOB-001",
            product_name="Marlboro Cigarettes",
            category="Tobacco",
            contains_tobacco=True,
        )
        result = validator.validate(product)

        assert result.is_deterministic is True
        assert result.is_eligible is False
        assert result.category == ClassificationCategory.INELIGIBLE_TOBACCO
        reasoning_text = " ".join(result.reasoning_chain).lower()
        assert "tobacco" in reasoning_text

    def test_hot_food_ineligible(self, validator: RuleValidator):
        """Test that hot food sold for immediate consumption is ineligible."""
        product = ProductInput(
            product_id="TEST-HOT-001",
            product_name="Hot Pizza Slice",
            category="Prepared Foods",
            is_hot_at_sale=True,
        )
        result = validator.validate(product)

        assert result.is_deterministic is True
        assert result.is_eligible is False
        assert result.category == ClassificationCategory.INELIGIBLE_HOT_FOOD
        reasoning_text = " ".join(result.reasoning_chain).lower()
        assert "hot" in reasoning_text

    def test_supplement_ineligible(self, validator: RuleValidator):
        """Test that supplements with supplement facts label are ineligible."""
        product = ProductInput(
            product_id="TEST-SUP-001",
            product_name="One A Day Multivitamin",
            category="Health",
            nutrition_label_type="supplement_facts",
        )
        result = validator.validate(product)

        assert result.is_deterministic is True
        assert result.is_eligible is False
        assert result.category == ClassificationCategory.INELIGIBLE_SUPPLEMENT
        reasoning_text = " ".join(result.reasoning_chain).lower()
        assert "supplement" in reasoning_text

    def test_cbd_ineligible(self, validator: RuleValidator):
        """Test that CBD/cannabis products are ineligible."""
        product = ProductInput(
            product_id="TEST-CBD-001",
            product_name="CBD Gummy Bears",
            category="Health",
            contains_cbd_cannabis=True,
        )
        result = validator.validate(product)

        assert result.is_deterministic is True
        assert result.is_eligible is False
        assert result.category == ClassificationCategory.INELIGIBLE_CBD_CANNABIS
        reasoning_text = " ".join(result.reasoning_chain).lower()
        assert "cbd" in reasoning_text or "cannabis" in reasoning_text

    def test_live_animal_ineligible(self, validator: RuleValidator):
        """Test that live animals are ineligible."""
        product = ProductInput(
            product_id="TEST-ANI-001",
            product_name="Live Chicken",
            category="Poultry",
            is_live_animal=True,
        )
        result = validator.validate(product)

        assert result.is_deterministic is True
        assert result.is_eligible is False
        assert result.category == ClassificationCategory.INELIGIBLE_LIVE_ANIMAL
        reasoning_text = " ".join(result.reasoning_chain).lower()
        assert "live" in reasoning_text or "animal" in reasoning_text

    def test_onsite_consumption_ineligible(self, validator: RuleValidator):
        """Test that food for on-site consumption is ineligible."""
        product = ProductInput(
            product_id="TEST-ONS-001",
            product_name="Restaurant Meal",
            category="Prepared Foods",
            is_for_onsite_consumption=True,
        )
        result = validator.validate(product)

        assert result.is_deterministic is True
        assert result.is_eligible is False
        assert result.category == ClassificationCategory.INELIGIBLE_ONSITE_CONSUMPTION

    def test_produce_eligible(self, validator: RuleValidator):
        """Test that fresh produce with nutrition facts is eligible."""
        product = ProductInput(
            product_id="TEST-PRO-001",
            product_name="Fresh Apples",
            category="Produce",
            nutrition_label_type="nutrition_facts",
        )
        result = validator.validate(product)

        assert result.is_deterministic is True
        assert result.is_eligible is True
        assert result.category == ClassificationCategory.ELIGIBLE_STAPLE_FOOD

    def test_beverage_with_nutrition_facts_eligible(self, validator: RuleValidator):
        """Test that beverages with nutrition facts label are eligible."""
        product = ProductInput(
            product_id="TEST-BEV-001",
            product_name="Coca-Cola Classic",
            category="Beverages",
            nutrition_label_type="nutrition_facts",
            alcohol_content=0.0,
        )
        result = validator.validate(product)

        assert result.is_deterministic is True
        assert result.is_eligible is True
        assert result.category == ClassificationCategory.ELIGIBLE_BEVERAGE

    def test_snack_eligible(self, validator: RuleValidator):
        """Test that snack foods with nutrition facts are eligible."""
        product = ProductInput(
            product_id="TEST-SNK-001",
            product_name="Snickers Bar",
            category="Snacks",
            nutrition_label_type="nutrition_facts",
        )
        result = validator.validate(product)

        assert result.is_deterministic is True
        assert result.is_eligible is True
        assert result.category == ClassificationCategory.ELIGIBLE_SNACK_FOOD

    def test_baby_food_eligible(self, validator: RuleValidator):
        """Test that baby food is eligible."""
        product = ProductInput(
            product_id="TEST-BAB-001",
            product_name="Gerber Baby Cereal",
            category="Baby Food",
            nutrition_label_type="nutrition_facts",
        )
        result = validator.validate(product)

        assert result.is_deterministic is True
        assert result.is_eligible is True
        assert result.category == ClassificationCategory.ELIGIBLE_BABY_FOOD

    def test_dairy_eligible(self, validator: RuleValidator):
        """Test that dairy products are eligible."""
        product = ProductInput(
            product_id="TEST-DAI-001",
            product_name="Organic Whole Milk",
            category="Dairy",
            nutrition_label_type="nutrition_facts",
        )
        result = validator.validate(product)

        assert result.is_deterministic is True
        assert result.is_eligible is True
        assert result.category == ClassificationCategory.ELIGIBLE_STAPLE_FOOD

    def test_meat_eligible(self, validator: RuleValidator):
        """Test that meat products are eligible."""
        product = ProductInput(
            product_id="TEST-MEA-001",
            product_name="Ground Beef",
            category="Meat",
            nutrition_label_type="nutrition_facts",
        )
        result = validator.validate(product)

        assert result.is_deterministic is True
        assert result.is_eligible is True
        assert result.category == ClassificationCategory.ELIGIBLE_STAPLE_FOOD

    def test_seafood_eligible(self, validator: RuleValidator):
        """Test that seafood is eligible."""
        product = ProductInput(
            product_id="TEST-SEA-001",
            product_name="Fresh Salmon Fillet",
            category="Seafood",
            nutrition_label_type="nutrition_facts",
        )
        result = validator.validate(product)

        assert result.is_deterministic is True
        assert result.is_eligible is True
        assert result.category == ClassificationCategory.ELIGIBLE_STAPLE_FOOD

    def test_seeds_plants_eligible(self, validator: RuleValidator):
        """Test that seeds and plants for food production are eligible."""
        product = ProductInput(
            product_id="TEST-SED-001",
            product_name="Vegetable Seeds Assortment",
            category="Seeds",
        )
        result = validator.validate(product)

        assert result.is_deterministic is True
        assert result.is_eligible is True
        assert result.category == ClassificationCategory.ELIGIBLE_SEEDS_PLANTS

    def test_unknown_product_ambiguous(self, validator: RuleValidator):
        """Test that unknown products require AI reasoning."""
        product = ProductInput(
            product_id="TEST-UNK-001",
            product_name="Mystery Item",
        )
        result = validator.validate(product)

        assert result.is_deterministic is False
        assert result.ambiguity_reason is not None

    def test_energy_drink_eligible(self, validator: RuleValidator):
        """Test that energy drinks with nutrition facts are eligible."""
        product = ProductInput(
            product_id="TEST-ENG-001",
            product_name="Monster Energy Drink",
            category="Beverages",
            nutrition_label_type="nutrition_facts",
            alcohol_content=0.0,
        )
        result = validator.validate(product)

        assert result.is_deterministic is True
        assert result.is_eligible is True
        assert result.category == ClassificationCategory.ELIGIBLE_BEVERAGE

    def test_cereal_eligible(self, validator: RuleValidator):
        """Test that cereals are eligible."""
        product = ProductInput(
            product_id="TEST-CER-001",
            product_name="Cheerios Cereal",
            category="Cereals",
            nutrition_label_type="nutrition_facts",
        )
        result = validator.validate(product)

        assert result.is_deterministic is True
        assert result.is_eligible is True
        assert result.category == ClassificationCategory.ELIGIBLE_STAPLE_FOOD

    def test_rule_priority_alcohol_over_category(self, validator: RuleValidator):
        """Test that alcohol rule takes priority over eligible category."""
        product = ProductInput(
            product_id="TEST-PRI-001",
            product_name="Wine",
            category="Beverages",  # Would be eligible category
            nutrition_label_type="nutrition_facts",
            alcohol_content=0.12,  # But has alcohol
        )
        result = validator.validate(product)

        assert result.is_deterministic is True
        assert result.is_eligible is False
        assert result.category == ClassificationCategory.INELIGIBLE_ALCOHOL

    def test_rule_priority_tobacco_over_category(self, validator: RuleValidator):
        """Test that tobacco rule takes priority over category."""
        product = ProductInput(
            product_id="TEST-PRI-002",
            product_name="Tobacco Product",
            category="Snacks",  # Incorrect category
            contains_tobacco=True,
        )
        result = validator.validate(product)

        assert result.is_deterministic is True
        assert result.is_eligible is False
        assert result.category == ClassificationCategory.INELIGIBLE_TOBACCO

    def test_key_factors_tracking(self, validator: RuleValidator):
        """Test that key factors are properly tracked."""
        product = ProductInput(
            product_id="TEST-TRK-001",
            product_name="Fresh Apples",
            category="Produce",
            nutrition_label_type="nutrition_facts",
        )
        result = validator.validate(product)

        assert result.key_factors is not None
        assert len(result.key_factors) > 0

    def test_regulation_citations_included(self, validator: RuleValidator):
        """Test that regulation citations are included."""
        product = ProductInput(
            product_id="TEST-CIT-001",
            product_name="Budweiser Beer",
            alcohol_content=0.05,
        )
        result = validator.validate(product)

        assert result.citations is not None
        assert len(result.citations) > 0
        # Should cite 7 CFR 271.2
        citations_text = " ".join([c.regulation_id for c in result.citations])
        assert "271.2" in citations_text or "CFR" in citations_text

    def test_reasoning_chain_populated(self, validator: RuleValidator):
        """Test that reasoning chain is populated."""
        product = ProductInput(
            product_id="TEST-RSN-001",
            product_name="Fresh Bananas",
            category="Produce",
            nutrition_label_type="nutrition_facts",
        )
        result = validator.validate(product)

        assert result.reasoning_chain is not None
        assert len(result.reasoning_chain) > 0
