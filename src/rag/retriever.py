"""Semantic search retrieval for SNAP regulations."""

from dataclasses import dataclass
from typing import List, Optional

from src.rag.vector_store import VectorStore, get_vector_store
from src.utils.logging import get_logger

logger = get_logger(__name__)


@dataclass
class RetrievedDocument:
    """A document retrieved from the vector store."""

    content: str
    metadata: dict
    relevance_score: float
    doc_id: str


class SNAPRegulationRetriever:
    """Retrieves relevant SNAP regulations using semantic search."""

    def __init__(self, vector_store: VectorStore = None):
        """
        Initialize retriever.

        Args:
            vector_store: Vector store instance
        """
        self.vector_store = vector_store or get_vector_store()

    def retrieve(
        self,
        query: str,
        k: int = 5,
        min_relevance: float = 0.0,
        doc_type: Optional[str] = None,
    ) -> List[RetrievedDocument]:
        """
        Retrieve relevant documents for a query.

        Args:
            query: Search query
            k: Number of documents to retrieve
            min_relevance: Minimum relevance score (0-1)
            doc_type: Optional filter by document type

        Returns:
            List of retrieved documents sorted by relevance
        """
        # Build filter if doc_type specified
        where_filter = None
        if doc_type:
            where_filter = {"doc_type": doc_type}

        # Query vector store
        results = self.vector_store.query(
            query_text=query,
            n_results=k,
            where=where_filter,
        )

        # Convert to RetrievedDocument objects
        documents = []
        for result in results:
            # Convert distance to relevance score (lower distance = higher relevance)
            # ChromaDB uses L2 distance by default
            distance = result.get("distance", 0)
            relevance_score = 1.0 / (1.0 + distance)

            if relevance_score >= min_relevance:
                documents.append(
                    RetrievedDocument(
                        content=result["document"],
                        metadata=result["metadata"],
                        relevance_score=relevance_score,
                        doc_id=result["id"],
                    )
                )

        # Sort by relevance (highest first)
        documents.sort(key=lambda x: x.relevance_score, reverse=True)

        logger.info(
            "documents_retrieved",
            query_length=len(query),
            results=len(documents),
        )

        return documents

    def retrieve_for_classification(
        self,
        product_name: str,
        category: Optional[str] = None,
        description: Optional[str] = None,
        k: int = 3,
    ) -> List[RetrievedDocument]:
        """
        Retrieve regulations relevant to a product classification.

        Args:
            product_name: Name of the product
            category: Product category
            description: Product description
            k: Number of documents to retrieve

        Returns:
            List of relevant documents
        """
        # Build a comprehensive query
        query_parts = [f"SNAP EBT eligibility for {product_name}"]

        if category:
            query_parts.append(f"category: {category}")

        if description:
            query_parts.append(description[:200])  # Limit description length

        query = " ".join(query_parts)

        return self.retrieve(query, k=k)

    def retrieve_by_category(
        self,
        category: str,
        k: int = 3,
    ) -> List[RetrievedDocument]:
        """
        Retrieve regulations for a product category.

        Args:
            category: Product category (e.g., "beverages", "supplements")
            k: Number of documents to retrieve

        Returns:
            List of relevant documents
        """
        # Category-specific queries
        category_queries = {
            "alcohol": "SNAP alcohol alcoholic beverages eligibility excluded",
            "tobacco": "SNAP tobacco products cigarettes eligibility excluded",
            "supplements": "SNAP supplements vitamins Supplement Facts label eligibility",
            "beverages": "SNAP beverages drinks non-alcoholic eligibility",
            "hot_food": "SNAP hot food prepared immediate consumption eligibility",
            "produce": "SNAP produce fruits vegetables staple food eligibility",
            "dairy": "SNAP dairy milk cheese yogurt staple food eligibility",
            "meat": "SNAP meat poultry fish seafood staple food eligibility",
            "snacks": "SNAP snacks candy cookies ice cream accessory food eligibility",
            "baby_food": "SNAP baby food infant formula eligibility",
            "seeds": "SNAP seeds plants food production eligibility",
        }

        query = category_queries.get(
            category.lower(),
            f"SNAP {category} food eligibility regulations",
        )

        return self.retrieve(query, k=k)

    def format_context(self, documents: List[RetrievedDocument]) -> str:
        """
        Format retrieved documents as context for the AI agent.

        Args:
            documents: List of retrieved documents

        Returns:
            Formatted context string
        """
        if not documents:
            return "No relevant regulations found."

        context_parts = ["Relevant SNAP Regulations:\n"]

        for i, doc in enumerate(documents, 1):
            source = doc.metadata.get("source", "Unknown")
            source_url = doc.metadata.get("source_url", "")

            context_parts.append(f"\n{i}. Source: {source}")
            if source_url:
                context_parts.append(f"   URL: {source_url}")
            context_parts.append(f"   Relevance: {doc.relevance_score:.2f}")
            context_parts.append(f"   Content:\n   {doc.content[:500]}...")

        return "\n".join(context_parts)


# Global retriever instance
_retriever: SNAPRegulationRetriever | None = None


def get_retriever() -> SNAPRegulationRetriever:
    """Get the global retriever instance."""
    global _retriever
    if _retriever is None:
        _retriever = SNAPRegulationRetriever()
    return _retriever
