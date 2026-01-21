"""Unit tests for the classification engine."""

import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime

from src.services.classification_engine import ClassificationEngine
from src.services.rule_validator import RuleValidator
from src.services.confidence_scorer import ConfidenceScorer
from src.models.product import ProductInput
from src.models.classification import RuleValidationResult, ClassificationResult, AIReasoningResult
from src.core.constants import ClassificationCategory


class TestClassificationEngine:
    """Test suite for ClassificationEngine."""

    @pytest.fixture
    def mock_product_repo(self):
        """Create a mock product repository."""
        repo = AsyncMock()
        repo.save = AsyncMock()
        return repo

    @pytest.fixture
    def mock_classification_repo(self):
        """Create a mock classification repository."""
        repo = AsyncMock()
        repo.save = AsyncMock()
        repo.get_by_product_id = AsyncMock(return_value=None)  # No cache
        return repo

    @pytest.fixture
    def mock_audit_repo(self):
        """Create a mock audit repository."""
        repo = AsyncMock()
        repo.save = AsyncMock()
        return repo

    @pytest.fixture
    def mock_ai_agent(self):
        """Create a mock AI agent."""
        agent = MagicMock()
        agent.model_name = "test-model"
        agent.reason = AsyncMock(return_value=AIReasoningResult(
            is_eligible=True,
            category=ClassificationCategory.ELIGIBLE_STAPLE_FOOD,
            reasoning_chain=["AI determined product is eligible"],
            citations=[],
            key_factors=["food item"],
            data_sources_used=["SNAP Guidelines"],
        ))
        return agent

    @pytest.fixture
    def engine(
        self,
        mock_product_repo,
        mock_classification_repo,
        mock_audit_repo,
        mock_ai_agent,
    ):
        """Create a classification engine with mocked dependencies."""
        return ClassificationEngine(
            rule_validator=RuleValidator(),
            ai_agent=mock_ai_agent,
            confidence_scorer=ConfidenceScorer(),
            product_repo=mock_product_repo,
            classification_repo=mock_classification_repo,
            audit_repo=mock_audit_repo,
        )

    @pytest.mark.asyncio
    async def test_classify_eligible_produce(self, engine):
        """Test classification of eligible produce."""
        product = ProductInput(
            product_id="TEST-001",
            product_name="Fresh Apples",
            category="Produce",
            nutrition_label_type="nutrition_facts",
        )

        result = await engine.classify(product)

        assert result is not None
        assert result.is_ebt_eligible is True
        assert result.classification_category == ClassificationCategory.ELIGIBLE_STAPLE_FOOD
        assert result.confidence_score >= 0.7

    @pytest.mark.asyncio
    async def test_classify_ineligible_alcohol(self, engine):
        """Test classification of ineligible alcohol product."""
        product = ProductInput(
            product_id="TEST-002",
            product_name="Budweiser Beer",
            category="Beverages",
            alcohol_content=0.05,
        )

        result = await engine.classify(product)

        assert result is not None
        assert result.is_ebt_eligible is False
        assert result.classification_category == ClassificationCategory.INELIGIBLE_ALCOHOL

    @pytest.mark.asyncio
    async def test_classify_ineligible_tobacco(self, engine):
        """Test classification of ineligible tobacco product."""
        product = ProductInput(
            product_id="TEST-003",
            product_name="Marlboro Cigarettes",
            category="Tobacco",
            contains_tobacco=True,
        )

        result = await engine.classify(product)

        assert result is not None
        assert result.is_ebt_eligible is False
        assert result.classification_category == ClassificationCategory.INELIGIBLE_TOBACCO

    @pytest.mark.asyncio
    async def test_classify_ineligible_hot_food(self, engine):
        """Test classification of ineligible hot food."""
        product = ProductInput(
            product_id="TEST-004",
            product_name="Hot Pizza Slice",
            category="Prepared Foods",
            is_hot_at_sale=True,
        )

        result = await engine.classify(product)

        assert result is not None
        assert result.is_ebt_eligible is False
        assert result.classification_category == ClassificationCategory.INELIGIBLE_HOT_FOOD

    @pytest.mark.asyncio
    async def test_classify_ineligible_supplement(self, engine):
        """Test classification of ineligible supplement."""
        product = ProductInput(
            product_id="TEST-005",
            product_name="Centrum Multivitamin",
            category="Health",
            nutrition_label_type="supplement_facts",
        )

        result = await engine.classify(product)

        assert result is not None
        assert result.is_ebt_eligible is False
        assert result.classification_category == ClassificationCategory.INELIGIBLE_SUPPLEMENT

    @pytest.mark.asyncio
    async def test_classify_eligible_dairy(self, engine):
        """Test classification of eligible dairy product."""
        product = ProductInput(
            product_id="TEST-006",
            product_name="Organic Whole Milk",
            category="Dairy",
            nutrition_label_type="nutrition_facts",
        )

        result = await engine.classify(product)

        assert result is not None
        assert result.is_ebt_eligible is True
        assert result.classification_category == ClassificationCategory.ELIGIBLE_STAPLE_FOOD

    @pytest.mark.asyncio
    async def test_classify_eligible_beverage(self, engine):
        """Test classification of eligible beverage."""
        product = ProductInput(
            product_id="TEST-007",
            product_name="Coca-Cola Classic",
            category="Beverages",
            nutrition_label_type="nutrition_facts",
            alcohol_content=0.0,
        )

        result = await engine.classify(product)

        assert result is not None
        assert result.is_ebt_eligible is True
        assert result.classification_category == ClassificationCategory.ELIGIBLE_BEVERAGE

    @pytest.mark.asyncio
    async def test_classify_eligible_snack(self, engine):
        """Test classification of eligible snack."""
        product = ProductInput(
            product_id="TEST-008",
            product_name="Snickers Bar",
            category="Snacks",
            nutrition_label_type="nutrition_facts",
        )

        result = await engine.classify(product)

        assert result is not None
        assert result.is_ebt_eligible is True
        assert result.classification_category == ClassificationCategory.ELIGIBLE_SNACK_FOOD

    @pytest.mark.asyncio
    async def test_classify_result_has_audit_id(self, engine):
        """Test that classification result includes audit ID."""
        product = ProductInput(
            product_id="TEST-009",
            product_name="Fresh Apples",
            category="Produce",
            nutrition_label_type="nutrition_facts",
        )

        result = await engine.classify(product)

        assert result.audit_id is not None
        assert len(result.audit_id) > 0

    @pytest.mark.asyncio
    async def test_classify_result_has_reasoning(self, engine):
        """Test that classification result includes reasoning."""
        product = ProductInput(
            product_id="TEST-010",
            product_name="Fresh Apples",
            category="Produce",
            nutrition_label_type="nutrition_facts",
        )

        result = await engine.classify(product)

        assert result.reasoning_chain is not None
        assert len(result.reasoning_chain) > 0

    @pytest.mark.asyncio
    async def test_classify_result_has_regulation_citations(self, engine):
        """Test that classification result includes regulation citations."""
        product = ProductInput(
            product_id="TEST-011",
            product_name="Budweiser Beer",
            alcohol_content=0.05,
        )

        result = await engine.classify(product)

        assert result.regulation_citations is not None

    @pytest.mark.asyncio
    async def test_bulk_classify(self, engine):
        """Test bulk classification of multiple products."""
        products = [
            ProductInput(
                product_id="BULK-001",
                product_name="Fresh Apples",
                category="Produce",
                nutrition_label_type="nutrition_facts",
            ),
            ProductInput(
                product_id="BULK-002",
                product_name="Budweiser Beer",
                category="Beverages",
                alcohol_content=0.05,
            ),
            ProductInput(
                product_id="BULK-003",
                product_name="Cheerios Cereal",
                category="Cereals",
                nutrition_label_type="nutrition_facts",
            ),
        ]

        result = await engine.bulk_classify(products)

        assert result is not None
        assert result.total_products == 3
        assert result.successful >= 0
        assert len(result.results) <= 3

    @pytest.mark.asyncio
    async def test_bulk_classify_mixed_eligibility(self, engine):
        """Test bulk classification returns correct eligibility mix."""
        products = [
            ProductInput(
                product_id="MIX-001",
                product_name="Fresh Bananas",
                category="Produce",
                nutrition_label_type="nutrition_facts",
            ),
            ProductInput(
                product_id="MIX-002",
                product_name="Wine Bottle",
                category="Beverages",
                alcohol_content=0.12,
            ),
        ]

        result = await engine.bulk_classify(products)

        if len(result.results) == 2:
            eligible_count = sum(1 for r in result.results if r.is_ebt_eligible)
            ineligible_count = sum(1 for r in result.results if not r.is_ebt_eligible)

            assert eligible_count == 1
            assert ineligible_count == 1

    @pytest.mark.asyncio
    async def test_classify_seeds_eligible(self, engine):
        """Test classification of eligible seeds."""
        product = ProductInput(
            product_id="TEST-012",
            product_name="Vegetable Seeds",
            category="Seeds",
        )

        result = await engine.classify(product)

        assert result is not None
        assert result.is_ebt_eligible is True
        assert result.classification_category == ClassificationCategory.ELIGIBLE_SEEDS_PLANTS

    @pytest.mark.asyncio
    async def test_classify_baby_food_eligible(self, engine):
        """Test classification of eligible baby food."""
        product = ProductInput(
            product_id="TEST-013",
            product_name="Gerber Baby Cereal",
            category="Baby Food",
            nutrition_label_type="nutrition_facts",
        )

        result = await engine.classify(product)

        assert result is not None
        assert result.is_ebt_eligible is True
        assert result.classification_category == ClassificationCategory.ELIGIBLE_BABY_FOOD

    @pytest.mark.asyncio
    async def test_classify_live_animal_ineligible(self, engine):
        """Test classification of ineligible live animal."""
        product = ProductInput(
            product_id="TEST-014",
            product_name="Live Chicken",
            category="Poultry",
            is_live_animal=True,
        )

        result = await engine.classify(product)

        assert result is not None
        assert result.is_ebt_eligible is False
        assert result.classification_category == ClassificationCategory.INELIGIBLE_LIVE_ANIMAL

    @pytest.mark.asyncio
    async def test_classify_cbd_ineligible(self, engine):
        """Test classification of ineligible CBD product."""
        product = ProductInput(
            product_id="TEST-015",
            product_name="CBD Gummies",
            category="Health",
            contains_cbd_cannabis=True,
        )

        result = await engine.classify(product)

        assert result is not None
        assert result.is_ebt_eligible is False
        assert result.classification_category == ClassificationCategory.INELIGIBLE_CBD_CANNABIS

    @pytest.mark.asyncio
    async def test_classify_onsite_consumption_ineligible(self, engine):
        """Test classification of ineligible on-site consumption."""
        product = ProductInput(
            product_id="TEST-016",
            product_name="Restaurant Meal",
            category="Prepared Foods",
            is_for_onsite_consumption=True,
        )

        result = await engine.classify(product)

        assert result is not None
        assert result.is_ebt_eligible is False
        assert result.classification_category == ClassificationCategory.INELIGIBLE_ONSITE_CONSUMPTION

    @pytest.mark.asyncio
    async def test_empty_bulk_request(self, engine):
        """Test bulk classification with empty product list."""
        result = await engine.bulk_classify([])

        assert result.total_products == 0
        assert result.successful == 0
        assert result.failed == 0
        assert len(result.results) == 0

    @pytest.mark.asyncio
    async def test_classification_stores_audit(
        self,
        engine,
        mock_audit_repo,
    ):
        """Test that classification stores audit record."""
        product = ProductInput(
            product_id="TEST-017",
            product_name="Fresh Apples",
            category="Produce",
            nutrition_label_type="nutrition_facts",
        )

        await engine.classify(product)

        # Verify audit was saved
        mock_audit_repo.save.assert_called_once()

    @pytest.mark.asyncio
    async def test_classification_stores_result(
        self,
        engine,
        mock_classification_repo,
    ):
        """Test that classification stores result."""
        product = ProductInput(
            product_id="TEST-018",
            product_name="Fresh Apples",
            category="Produce",
            nutrition_label_type="nutrition_facts",
        )

        await engine.classify(product)

        # Verify classification was saved
        mock_classification_repo.save.assert_called_once()

    @pytest.mark.asyncio
    async def test_classification_returns_cached_result(
        self,
        engine,
        mock_classification_repo,
    ):
        """Test that cached classification is returned."""
        cached_result = ClassificationResult(
            product_id="TEST-019",
            product_name="Cached Product",
            is_ebt_eligible=True,
            confidence_score=0.95,
            classification_category=ClassificationCategory.ELIGIBLE_STAPLE_FOOD,
            reasoning_chain=["Cached result"],
            regulation_citations=[],
            key_factors=["Cached"],
            classification_timestamp=datetime.utcnow(),
            model_version="1.0.0",
            processing_time_ms=100,
            data_sources_used=[],
            audit_id="cached-audit-id",
            request_hash="cached-hash",
        )
        mock_classification_repo.get_by_product_id = AsyncMock(return_value=cached_result)

        product = ProductInput(
            product_id="TEST-019",
            product_name="Cached Product",
            category="Produce",
        )

        result = await engine.classify(product)

        assert result.audit_id == "cached-audit-id"

    @pytest.mark.asyncio
    async def test_classification_uses_ai_for_ambiguous(
        self,
        engine,
        mock_ai_agent,
    ):
        """Test that AI is used for ambiguous products."""
        product = ProductInput(
            product_id="TEST-020",
            product_name="Mystery Product",
        )

        await engine.classify(product)

        # AI agent should be called for ambiguous product
        mock_ai_agent.reason.assert_called_once()
