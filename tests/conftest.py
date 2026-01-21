"""Pytest fixtures and configuration."""

import asyncio
import os
import sys
from pathlib import Path
from typing import AsyncGenerator

import pytest
import pytest_asyncio
from httpx import AsyncClient

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.data.database import Database, initialize_database
from src.main import app


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture
async def test_db() -> AsyncGenerator[Database, None]:
    """Create a test database."""
    # Use in-memory database for tests
    db = Database(":memory:")
    await initialize_database(db)
    yield db


@pytest_asyncio.fixture
async def async_client() -> AsyncGenerator[AsyncClient, None]:
    """Create async HTTP client for API tests."""
    # Initialize database before tests
    db = Database(":memory:")
    await initialize_database(db)

    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client


@pytest.fixture
def sample_product_data() -> dict:
    """Sample product data for testing."""
    return {
        "product_id": "TEST-001",
        "product_name": "Test Product",
        "category": "Beverages",
        "brand": "Test Brand",
        "nutrition_label_type": "nutrition_facts",
        "is_hot_at_sale": False,
        "alcohol_content": 0.0,
        "contains_tobacco": False,
        "contains_cbd_cannabis": False,
        "is_live_animal": False,
    }


@pytest.fixture
def eligible_product_data() -> dict:
    """Sample eligible product data."""
    return {
        "product_id": "ELIG-001",
        "product_name": "Fresh Apples",
        "category": "Produce",
        "nutrition_label_type": "nutrition_facts",
    }


@pytest.fixture
def ineligible_alcohol_data() -> dict:
    """Sample ineligible alcohol product data."""
    return {
        "product_id": "INALC-001",
        "product_name": "Budweiser Beer",
        "category": "Beverages",
        "alcohol_content": 0.05,
    }


@pytest.fixture
def ineligible_tobacco_data() -> dict:
    """Sample ineligible tobacco product data."""
    return {
        "product_id": "INTOB-001",
        "product_name": "Marlboro Red",
        "category": "Tobacco",
        "contains_tobacco": True,
    }


@pytest.fixture
def ineligible_supplement_data() -> dict:
    """Sample ineligible supplement product data."""
    return {
        "product_id": "INSUP-001",
        "product_name": "Centrum Multivitamin",
        "category": "Health",
        "nutrition_label_type": "supplement_facts",
    }


@pytest.fixture
def ineligible_hot_food_data() -> dict:
    """Sample ineligible hot food product data."""
    return {
        "product_id": "INHOT-001",
        "product_name": "Rotisserie Chicken",
        "category": "Prepared Foods",
        "is_hot_at_sale": True,
    }


@pytest.fixture
def ineligible_cbd_data() -> dict:
    """Sample ineligible CBD product data."""
    return {
        "product_id": "INCBD-001",
        "product_name": "CBD Gummies",
        "category": "Health",
        "contains_cbd_cannabis": True,
    }


@pytest.fixture
def ineligible_live_animal_data() -> dict:
    """Sample ineligible live animal product data."""
    return {
        "product_id": "INANI-001",
        "product_name": "Live Chicken",
        "category": "Poultry",
        "is_live_animal": True,
    }


@pytest.fixture
def ambiguous_product_data() -> dict:
    """Sample ambiguous product data (needs AI)."""
    return {
        "product_id": "AMB-001",
        "product_name": "Mystery Item",
        "description": "An item of unknown type",
    }


@pytest.fixture
def bulk_products_data() -> list:
    """Sample bulk products for testing."""
    return [
        {"product_id": "BULK-001", "product_name": "Bananas", "category": "Produce"},
        {"product_id": "BULK-002", "product_name": "Beer", "category": "Beverages", "alcohol_content": 0.05},
        {"product_id": "BULK-003", "product_name": "Cigarettes", "category": "Tobacco", "contains_tobacco": True},
    ]
