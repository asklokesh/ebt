"""Integration tests for RAG retrieval system."""

import pytest
import pytest_asyncio
from pathlib import Path
from unittest.mock import AsyncMock, patch, MagicMock

from src.rag.retriever import SNAPRegulationRetriever
from src.rag.vector_store import VectorStore
from src.rag.document_loader import RegulationDocumentLoader
from src.models.product import ProductInput


class TestRegulationDocumentLoader:
    """Test suite for RegulationDocumentLoader."""

    @pytest.fixture
    def loader(self):
        """Create a document loader instance."""
        return RegulationDocumentLoader()

    def test_loader_initialization(self, loader):
        """Test that loader initializes correctly."""
        assert loader is not None

    def test_load_regulations_returns_documents(self, loader):
        """Test that loading regulations returns documents."""
        docs = loader.load_regulations()

        assert docs is not None
        assert isinstance(docs, list)

    def test_documents_have_content(self, loader):
        """Test that loaded documents have content."""
        docs = loader.load_regulations()

        if docs:  # Only test if documents exist
            for doc in docs:
                assert hasattr(doc, "page_content") or hasattr(doc, "content")

    def test_documents_have_metadata(self, loader):
        """Test that loaded documents have metadata."""
        docs = loader.load_regulations()

        if docs:
            for doc in docs:
                assert hasattr(doc, "metadata")


class TestVectorStore:
    """Test suite for VectorStore."""

    @pytest.fixture
    def vector_store(self):
        """Create a vector store instance."""
        return VectorStore()

    def test_vector_store_initialization(self, vector_store):
        """Test that vector store initializes correctly."""
        assert vector_store is not None

    def test_similarity_search_returns_results(self, vector_store):
        """Test that similarity search returns results."""
        results = vector_store.similarity_search("eligible foods SNAP", k=3)

        assert results is not None
        assert isinstance(results, list)

    def test_similarity_search_alcohol(self, vector_store):
        """Test similarity search for alcohol regulations."""
        results = vector_store.similarity_search(
            "alcoholic beverages ineligible SNAP", k=3
        )

        assert results is not None

    def test_similarity_search_tobacco(self, vector_store):
        """Test similarity search for tobacco regulations."""
        results = vector_store.similarity_search(
            "tobacco products not eligible", k=3
        )

        assert results is not None

    def test_similarity_search_supplements(self, vector_store):
        """Test similarity search for supplement regulations."""
        results = vector_store.similarity_search(
            "dietary supplements vitamins ineligible", k=3
        )

        assert results is not None


class TestSNAPRegulationRetriever:
    """Test suite for SNAPRegulationRetriever."""

    @pytest.fixture
    def retriever(self):
        """Create a retriever instance."""
        return SNAPRegulationRetriever()

    def test_retriever_initialization(self, retriever):
        """Test that retriever initializes correctly."""
        assert retriever is not None

    @pytest.mark.asyncio
    async def test_retrieve_for_produce(self, retriever):
        """Test retrieval for produce product."""
        product = ProductInput(
            product_id="RAG-001",
            product_name="Fresh Apples",
            category="Produce",
        )

        results = await retriever.retrieve_for_classification(product)

        assert results is not None
        assert isinstance(results, list)

    @pytest.mark.asyncio
    async def test_retrieve_for_alcohol(self, retriever):
        """Test retrieval for alcohol product."""
        product = ProductInput(
            product_id="RAG-002",
            product_name="Budweiser Beer",
            category="Beverages",
            alcohol_content=0.05,
        )

        results = await retriever.retrieve_for_classification(product)

        assert results is not None

    @pytest.mark.asyncio
    async def test_retrieve_for_tobacco(self, retriever):
        """Test retrieval for tobacco product."""
        product = ProductInput(
            product_id="RAG-003",
            product_name="Marlboro Cigarettes",
            contains_tobacco=True,
        )

        results = await retriever.retrieve_for_classification(product)

        assert results is not None

    @pytest.mark.asyncio
    async def test_retrieve_for_supplement(self, retriever):
        """Test retrieval for supplement product."""
        product = ProductInput(
            product_id="RAG-004",
            product_name="Centrum Multivitamin",
            nutrition_label_type="supplement_facts",
        )

        results = await retriever.retrieve_for_classification(product)

        assert results is not None

    @pytest.mark.asyncio
    async def test_retrieve_for_hot_food(self, retriever):
        """Test retrieval for hot food product."""
        product = ProductInput(
            product_id="RAG-005",
            product_name="Hot Pizza Slice",
            is_hot_at_sale=True,
        )

        results = await retriever.retrieve_for_classification(product)

        assert results is not None

    @pytest.mark.asyncio
    async def test_retrieve_returns_regulation_text(self, retriever):
        """Test that retrieval returns regulation text."""
        product = ProductInput(
            product_id="RAG-006",
            product_name="Test Product",
        )

        results = await retriever.retrieve_for_classification(product)

        assert results is not None
        # Results should be strings containing regulation text
        for result in results:
            assert isinstance(result, str)

    @pytest.mark.asyncio
    async def test_retrieve_limit_results(self, retriever):
        """Test that retrieval respects result limit."""
        product = ProductInput(
            product_id="RAG-007",
            product_name="Fresh Milk",
            category="Dairy",
        )

        results = await retriever.retrieve_for_classification(product, k=2)

        assert results is not None
        assert len(results) <= 2

    @pytest.mark.asyncio
    async def test_build_query_includes_product_name(self, retriever):
        """Test that query includes product name."""
        product = ProductInput(
            product_id="RAG-008",
            product_name="Organic Whole Milk",
        )

        query = retriever._build_query(product)

        assert "Organic Whole Milk" in query or "milk" in query.lower()

    @pytest.mark.asyncio
    async def test_build_query_includes_category(self, retriever):
        """Test that query includes category."""
        product = ProductInput(
            product_id="RAG-009",
            product_name="Test Product",
            category="Dairy",
        )

        query = retriever._build_query(product)

        assert "Dairy" in query or "dairy" in query.lower()

    @pytest.mark.asyncio
    async def test_build_query_for_alcohol_product(self, retriever):
        """Test query building for alcohol product."""
        product = ProductInput(
            product_id="RAG-010",
            product_name="Wine",
            alcohol_content=0.12,
        )

        query = retriever._build_query(product)

        assert "alcohol" in query.lower() or "wine" in query.lower()


class TestRAGIntegration:
    """Integration tests for the complete RAG system."""

    @pytest.fixture
    def retriever(self):
        """Create a retriever instance."""
        return SNAPRegulationRetriever()

    @pytest.mark.asyncio
    async def test_end_to_end_eligible_product(self, retriever):
        """Test end-to-end RAG for eligible product."""
        product = ProductInput(
            product_id="E2E-001",
            product_name="Fresh Organic Apples",
            category="Produce",
        )

        results = await retriever.retrieve_for_classification(product)

        assert results is not None
        # Should return relevant regulation context
        assert len(results) > 0

    @pytest.mark.asyncio
    async def test_end_to_end_ineligible_alcohol(self, retriever):
        """Test end-to-end RAG for ineligible alcohol."""
        product = ProductInput(
            product_id="E2E-002",
            product_name="Budweiser Beer 6-Pack",
            category="Beverages",
            alcohol_content=0.05,
        )

        results = await retriever.retrieve_for_classification(product)

        assert results is not None

    @pytest.mark.asyncio
    async def test_end_to_end_ambiguous_product(self, retriever):
        """Test end-to-end RAG for ambiguous product."""
        product = ProductInput(
            product_id="E2E-003",
            product_name="Energy Supplement Drink",
            category="Beverages",
        )

        results = await retriever.retrieve_for_classification(product)

        assert results is not None
        # Should return relevant context to help with classification

    @pytest.mark.asyncio
    async def test_regulation_context_quality(self, retriever):
        """Test that retrieved context is relevant."""
        product = ProductInput(
            product_id="E2E-004",
            product_name="Vitamin D Supplement",
            nutrition_label_type="supplement_facts",
        )

        results = await retriever.retrieve_for_classification(product)

        assert results is not None
        # Check that results contain relevant regulation text
        combined_text = " ".join(results).lower()
        # Should contain regulation-related content
        assert any(term in combined_text for term in [
            "eligible", "ineligible", "snap", "food", "supplement", "cfr", "271"
        ])
