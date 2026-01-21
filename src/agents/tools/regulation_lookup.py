"""RAG tool for looking up SNAP regulations."""

from typing import List, Optional

from src.rag.retriever import RetrievedDocument, SNAPRegulationRetriever, get_retriever
from src.utils.logging import get_logger

logger = get_logger(__name__)


class RegulationLookupTool:
    """Tool for looking up SNAP regulations using semantic search."""

    name: str = "regulation_lookup"
    description: str = (
        "Search SNAP regulations and FNS guidance for eligibility rules. "
        "Use this to find relevant regulations for product classification. "
        "Input should be a search query about SNAP eligibility."
    )

    def __init__(self, retriever: SNAPRegulationRetriever = None):
        """
        Initialize the regulation lookup tool.

        Args:
            retriever: Retriever instance for semantic search
        """
        self.retriever = retriever or get_retriever()

    def run(self, query: str) -> str:
        """
        Execute the regulation lookup.

        Args:
            query: Search query

        Returns:
            Formatted string of relevant regulations
        """
        logger.info("regulation_lookup", query=query)

        try:
            docs = self.retriever.retrieve(query, k=3)
            return self._format_results(docs)
        except Exception as e:
            logger.error("regulation_lookup_failed", error=str(e))
            return f"Error searching regulations: {str(e)}"

    async def arun(self, query: str) -> str:
        """
        Async execution of regulation lookup.

        Args:
            query: Search query

        Returns:
            Formatted string of relevant regulations
        """
        # For now, just wrap the sync version
        return self.run(query)

    def _format_results(self, docs: List[RetrievedDocument]) -> str:
        """
        Format retrieved documents as a string.

        Args:
            docs: List of retrieved documents

        Returns:
            Formatted string
        """
        if not docs:
            return "No relevant regulations found."

        result_parts = ["Relevant SNAP Regulations:\n"]

        for i, doc in enumerate(docs, 1):
            source = doc.metadata.get("source", "Unknown")
            source_url = doc.metadata.get("source_url", "")

            result_parts.append(f"\n{i}. Source: {source}")
            if source_url:
                result_parts.append(f"   URL: {source_url}")
            result_parts.append(f"   Relevance: {doc.relevance_score:.2f}")
            result_parts.append(f"   Content:\n   {doc.content[:500]}...")
            if len(doc.content) > 500:
                result_parts.append("   [truncated]")

        return "\n".join(result_parts)

    def lookup_by_category(self, category: str) -> str:
        """
        Lookup regulations for a specific product category.

        Args:
            category: Product category (e.g., "alcohol", "supplements")

        Returns:
            Formatted string of relevant regulations
        """
        docs = self.retriever.retrieve_by_category(category, k=3)
        return self._format_results(docs)

    def lookup_for_product(
        self,
        product_name: str,
        category: Optional[str] = None,
        description: Optional[str] = None,
    ) -> str:
        """
        Lookup regulations relevant to a specific product.

        Args:
            product_name: Name of the product
            category: Product category
            description: Product description

        Returns:
            Formatted string of relevant regulations
        """
        docs = self.retriever.retrieve_for_classification(
            product_name=product_name,
            category=category,
            description=description,
            k=3,
        )
        return self._format_results(docs)
