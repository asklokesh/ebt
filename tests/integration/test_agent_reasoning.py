"""Integration tests for AI agent reasoning."""

import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, patch, MagicMock

from src.agents.classification_agent import ClassificationAgent
from src.models.product import ProductInput
from src.models.classification import AIReasoningResult
from src.core.constants import ClassificationCategory


class TestClassificationAgent:
    """Test suite for ClassificationAgent."""

    @pytest.fixture
    def agent(self):
        """Create a classification agent instance."""
        return ClassificationAgent()

    @pytest.mark.asyncio
    async def test_agent_initialization(self, agent):
        """Test that agent initializes correctly."""
        assert agent is not None

    @pytest.mark.asyncio
    async def test_fallback_classification_produce(self, agent):
        """Test fallback classification for produce."""
        product = ProductInput(
            product_id="AGENT-001",
            product_name="Fresh Organic Apples",
            category="Produce",
        )

        # Test the fallback method directly
        result = agent._fallback_classification(product)

        assert result is not None
        assert result.is_eligible is True
        assert result.category == ClassificationCategory.ELIGIBLE_STAPLE_FOOD

    @pytest.mark.asyncio
    async def test_fallback_classification_alcohol(self, agent):
        """Test fallback classification for alcohol product."""
        product = ProductInput(
            product_id="AGENT-002",
            product_name="Budweiser Beer",
            category="Beverages",
            alcohol_content=0.05,
        )

        result = agent._fallback_classification(product)

        assert result is not None
        assert result.is_eligible is False
        assert result.category == ClassificationCategory.INELIGIBLE_ALCOHOL

    @pytest.mark.asyncio
    async def test_fallback_classification_tobacco(self, agent):
        """Test fallback classification for tobacco product."""
        product = ProductInput(
            product_id="AGENT-003",
            product_name="Marlboro Cigarettes",
            contains_tobacco=True,
        )

        result = agent._fallback_classification(product)

        assert result is not None
        assert result.is_eligible is False
        assert result.category == ClassificationCategory.INELIGIBLE_TOBACCO

    @pytest.mark.asyncio
    async def test_fallback_classification_supplement(self, agent):
        """Test fallback classification for supplement."""
        product = ProductInput(
            product_id="AGENT-004",
            product_name="Centrum Multivitamin",
            nutrition_label_type="supplement_facts",
        )

        result = agent._fallback_classification(product)

        assert result is not None
        assert result.is_eligible is False
        assert result.category == ClassificationCategory.INELIGIBLE_SUPPLEMENT

    @pytest.mark.asyncio
    async def test_fallback_classification_hot_food(self, agent):
        """Test fallback classification for hot food."""
        product = ProductInput(
            product_id="AGENT-005",
            product_name="Hot Pizza",
            is_hot_at_sale=True,
        )

        result = agent._fallback_classification(product)

        assert result is not None
        assert result.is_eligible is False
        assert result.category == ClassificationCategory.INELIGIBLE_HOT_FOOD

    @pytest.mark.asyncio
    async def test_fallback_classification_cbd(self, agent):
        """Test fallback classification for CBD product."""
        product = ProductInput(
            product_id="AGENT-006",
            product_name="CBD Gummies",
            contains_cbd_cannabis=True,
        )

        result = agent._fallback_classification(product)

        assert result is not None
        assert result.is_eligible is False
        assert result.category == ClassificationCategory.INELIGIBLE_CBD_CANNABIS

    @pytest.mark.asyncio
    async def test_fallback_classification_live_animal(self, agent):
        """Test fallback classification for live animal."""
        product = ProductInput(
            product_id="AGENT-007",
            product_name="Live Chicken",
            is_live_animal=True,
        )

        result = agent._fallback_classification(product)

        assert result is not None
        assert result.is_eligible is False
        assert result.category == ClassificationCategory.INELIGIBLE_LIVE_ANIMAL

    @pytest.mark.asyncio
    async def test_fallback_classification_dairy(self, agent):
        """Test fallback classification for dairy."""
        product = ProductInput(
            product_id="AGENT-008",
            product_name="Organic Milk",
            category="Dairy",
        )

        result = agent._fallback_classification(product)

        assert result is not None
        assert result.is_eligible is True
        assert result.category == ClassificationCategory.ELIGIBLE_STAPLE_FOOD

    @pytest.mark.asyncio
    async def test_fallback_classification_beverage(self, agent):
        """Test fallback classification for beverage."""
        product = ProductInput(
            product_id="AGENT-009",
            product_name="Coca-Cola",
            category="Beverages",
            nutrition_label_type="nutrition_facts",
        )

        result = agent._fallback_classification(product)

        assert result is not None
        assert result.is_eligible is True
        assert result.category == ClassificationCategory.ELIGIBLE_BEVERAGE

    @pytest.mark.asyncio
    async def test_fallback_classification_snack(self, agent):
        """Test fallback classification for snack."""
        product = ProductInput(
            product_id="AGENT-010",
            product_name="Snickers Bar",
            category="Snacks",
        )

        result = agent._fallback_classification(product)

        assert result is not None
        assert result.is_eligible is True
        assert result.category == ClassificationCategory.ELIGIBLE_SNACK_FOOD

    @pytest.mark.asyncio
    async def test_fallback_classification_baby_food(self, agent):
        """Test fallback classification for baby food."""
        product = ProductInput(
            product_id="AGENT-011",
            product_name="Gerber Baby Food",
            category="Baby Food",
        )

        result = agent._fallback_classification(product)

        assert result is not None
        assert result.is_eligible is True
        assert result.category == ClassificationCategory.ELIGIBLE_BABY_FOOD

    @pytest.mark.asyncio
    async def test_fallback_classification_unknown(self, agent):
        """Test fallback classification for unknown product."""
        product = ProductInput(
            product_id="AGENT-012",
            product_name="Mystery Item",
        )

        result = agent._fallback_classification(product)

        assert result is not None
        # Unknown products default to eligible staple food with low confidence
        assert result.category in [
            ClassificationCategory.ELIGIBLE_STAPLE_FOOD,
            ClassificationCategory.AMBIGUOUS,
        ]

    @pytest.mark.asyncio
    async def test_build_prompt(self, agent):
        """Test prompt building for AI classification."""
        product = ProductInput(
            product_id="AGENT-013",
            product_name="Test Product",
            category="Test Category",
            description="A test product description",
        )

        prompt = agent._build_classification_prompt(product, [])

        assert prompt is not None
        assert "Test Product" in prompt
        assert "Test Category" in prompt

    @pytest.mark.asyncio
    async def test_parse_ai_response_eligible(self, agent):
        """Test parsing AI response for eligible product."""
        response_text = """
        CLASSIFICATION: ELIGIBLE
        CATEGORY: ELIGIBLE_STAPLE_FOOD
        CONFIDENCE: 0.95

        REASONING:
        1. Product is a food item
        2. No alcohol content
        3. No tobacco
        4. Not sold hot

        KEY FACTORS:
        - Food product
        - Clearly eligible category

        REGULATION MATCHES:
        - 7 CFR 271.2: Staple foods are eligible
        """

        result = agent._parse_ai_response(response_text)

        assert result is not None
        assert result.is_eligible is True
        assert result.category == ClassificationCategory.ELIGIBLE_STAPLE_FOOD

    @pytest.mark.asyncio
    async def test_parse_ai_response_ineligible(self, agent):
        """Test parsing AI response for ineligible product."""
        response_text = """
        CLASSIFICATION: INELIGIBLE
        CATEGORY: INELIGIBLE_ALCOHOL
        CONFIDENCE: 0.98

        REASONING:
        1. Product contains alcohol
        2. Alcohol content exceeds 0.5% threshold

        KEY FACTORS:
        - Contains alcohol
        - Beer product

        REGULATION MATCHES:
        - 7 CFR 271.2: Alcoholic beverages are not eligible
        """

        result = agent._parse_ai_response(response_text)

        assert result is not None
        assert result.is_eligible is False
        assert result.category == ClassificationCategory.INELIGIBLE_ALCOHOL

    @pytest.mark.asyncio
    async def test_classify_without_llm_uses_fallback(self, agent):
        """Test that classification uses fallback when LLM is unavailable."""
        # Ensure LLM is not configured
        agent.llm = None

        product = ProductInput(
            product_id="AGENT-014",
            product_name="Fresh Apples",
            category="Produce",
        )

        result = await agent.classify(product, [])

        assert result is not None
        assert result.is_eligible is True
        assert result.category == ClassificationCategory.ELIGIBLE_STAPLE_FOOD

    @pytest.mark.asyncio
    async def test_reasoning_chain_populated(self, agent):
        """Test that reasoning chain is populated in result."""
        product = ProductInput(
            product_id="AGENT-015",
            product_name="Fresh Bananas",
            category="Produce",
        )

        result = await agent.classify(product, [])

        assert result is not None
        assert result.reasoning_chain is not None
        assert len(result.reasoning_chain) > 0

    @pytest.mark.asyncio
    async def test_key_factors_populated(self, agent):
        """Test that key factors are populated in result."""
        product = ProductInput(
            product_id="AGENT-016",
            product_name="Budweiser Beer",
            alcohol_content=0.05,
        )

        result = await agent.classify(product, [])

        assert result is not None
        assert result.key_factors is not None


class TestAgentPromptConstruction:
    """Test suite for agent prompt construction."""

    @pytest.fixture
    def agent(self):
        """Create a classification agent instance."""
        return ClassificationAgent()

    def test_prompt_includes_product_name(self, agent):
        """Test that prompt includes product name."""
        product = ProductInput(
            product_id="PROMPT-001",
            product_name="Organic Whole Milk",
        )

        prompt = agent._build_classification_prompt(product, [])

        assert "Organic Whole Milk" in prompt

    def test_prompt_includes_category(self, agent):
        """Test that prompt includes category if provided."""
        product = ProductInput(
            product_id="PROMPT-002",
            product_name="Test Product",
            category="Dairy",
        )

        prompt = agent._build_classification_prompt(product, [])

        assert "Dairy" in prompt

    def test_prompt_includes_alcohol_content(self, agent):
        """Test that prompt includes alcohol content if provided."""
        product = ProductInput(
            product_id="PROMPT-003",
            product_name="Beer",
            alcohol_content=0.05,
        )

        prompt = agent._build_classification_prompt(product, [])

        assert "alcohol" in prompt.lower() or "0.05" in prompt

    def test_prompt_includes_regulations(self, agent):
        """Test that prompt includes regulation context."""
        product = ProductInput(
            product_id="PROMPT-004",
            product_name="Test Product",
        )

        regulations = [
            "7 CFR 271.2 defines eligible foods",
            "Alcoholic beverages are not eligible",
        ]

        prompt = agent._build_classification_prompt(product, regulations)

        assert "271.2" in prompt or "regulation" in prompt.lower()
