"""FastAPI dependency injection."""

from typing import AsyncGenerator

from src.data.database import Database, get_database, initialize_database
from src.data.repositories.audit_repo import AuditRepository
from src.data.repositories.classification_repo import ClassificationRepository
from src.data.repositories.product_repo import ProductRepository
from src.services.challenge_handler import ChallengeHandler, get_challenge_handler
from src.services.classification_engine import ClassificationEngine, get_classification_engine
from src.utils.logging import get_logger

logger = get_logger(__name__)


async def get_db() -> Database:
    """
    Get database instance.

    Returns:
        Database instance
    """
    return get_database()


async def get_product_repository() -> ProductRepository:
    """
    Get product repository instance.

    Returns:
        ProductRepository instance
    """
    return ProductRepository()


async def get_classification_repository() -> ClassificationRepository:
    """
    Get classification repository instance.

    Returns:
        ClassificationRepository instance
    """
    return ClassificationRepository()


async def get_audit_repository() -> AuditRepository:
    """
    Get audit repository instance.

    Returns:
        AuditRepository instance
    """
    return AuditRepository()


def get_engine() -> ClassificationEngine:
    """
    Get classification engine instance.

    Returns:
        ClassificationEngine instance
    """
    return get_classification_engine()


def get_cloud_engine(api_key: str) -> ClassificationEngine:
    """
    Get a classification engine configured for cloud LLM.

    Args:
        api_key: Cloud API key

    Returns:
        ClassificationEngine with cloud LLM
    """
    from src.agents.classification_agent import ClassificationAgent
    from src.services.ai_reasoning_agent import AIReasoningAgent
    from src.core.config import settings

    # Create a cloud-configured classification agent
    class CloudAIReasoningAgent(AIReasoningAgent):
        def __init__(self, api_key: str):
            super().__init__()
            self.cloud_api_key = api_key
            self._agent = None

        @property
        def agent(self):
            if self._agent is None:
                self._agent = ClassificationAgent(
                    retriever=self.retriever,
                    model_name=settings.ollama_cloud_model,
                )
                # Override the LLM with cloud configuration
                from langchain_openai import ChatOpenAI
                self._agent.llm = ChatOpenAI(
                    model=settings.ollama_cloud_model,
                    api_key=self.cloud_api_key,
                    base_url=settings.ollama_cloud_base_url,
                    temperature=0.1,
                )
            return self._agent

    cloud_agent = CloudAIReasoningAgent(api_key)
    return ClassificationEngine(ai_agent=cloud_agent)


async def get_challenger() -> ChallengeHandler:
    """
    Get challenge handler instance.

    Returns:
        ChallengeHandler instance
    """
    return get_challenge_handler()


async def startup_event() -> None:
    """
    Application startup event handler.

    Initializes database and other resources.
    """
    logger.info("application_starting")

    # Initialize database
    db = get_database()
    await initialize_database(db)

    logger.info("application_started")


async def shutdown_event() -> None:
    """
    Application shutdown event handler.

    Cleans up resources.
    """
    logger.info("application_shutting_down")
    logger.info("application_shutdown_complete")
