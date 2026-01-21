"""AI reasoning agent wrapper service."""

from typing import Optional

from src.agents.classification_agent import ClassificationAgent
from src.core.config import settings
from src.models.classification import AIReasoningResult, RuleValidationResult
from src.models.product import ProductInput
from src.rag.retriever import SNAPRegulationRetriever, get_retriever
from src.utils.logging import get_logger

logger = get_logger(__name__)


class AIReasoningAgent:
    """
    Wrapper service for the AI classification agent.

    Provides a clean interface for the classification engine to use
    AI-based reasoning when rule-based validation is inconclusive.
    """

    def __init__(
        self,
        retriever: SNAPRegulationRetriever = None,
        model_name: str = None,
    ):
        """
        Initialize the AI reasoning agent.

        Args:
            retriever: RAG retriever for regulations
            model_name: LLM model name
        """
        self.model_name = model_name or settings.gemini_model
        self.retriever = retriever or get_retriever()
        self._agent = None

    @property
    def agent(self) -> ClassificationAgent:
        """Lazy load the classification agent."""
        if self._agent is None:
            self._agent = ClassificationAgent(
                retriever=self.retriever,
                model_name=self.model_name,
            )
        return self._agent

    async def reason(
        self,
        product: ProductInput,
        partial_rule_result: Optional[RuleValidationResult] = None,
    ) -> AIReasoningResult:
        """
        Use AI reasoning to classify a product.

        Args:
            product: Product to classify
            partial_rule_result: Partial result from rule-based validation

        Returns:
            AIReasoningResult with classification details
        """
        logger.info(
            "ai_reasoning_requested",
            product_id=product.product_id,
        )

        return await self.agent.reason(
            product=product,
            partial_rule_result=partial_rule_result,
        )

    def is_available(self) -> bool:
        """Check if AI reasoning is available."""
        return settings.is_gemini_configured or settings.ollama_enabled
