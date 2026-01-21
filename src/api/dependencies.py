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


async def get_engine() -> ClassificationEngine:
    """
    Get classification engine instance.

    Returns:
        ClassificationEngine instance
    """
    return get_classification_engine()


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
