"""Tool for looking up product information from external APIs."""

from typing import Any, Dict, Optional

from src.utils.logging import get_logger

logger = get_logger(__name__)


class ProductLookupTool:
    """Tool for looking up product information from external APIs."""

    name: str = "product_lookup"
    description: str = (
        "Look up product information from external databases like USDA FoodData Central "
        "or Open Food Facts. Input should be a UPC code or product name."
    )

    def __init__(self):
        """Initialize the product lookup tool."""
        self._usda_client = None
        self._openfoodfacts_client = None

    def run(self, query: str) -> str:
        """
        Execute the product lookup.

        Args:
            query: UPC code or product name

        Returns:
            Formatted string of product information
        """
        logger.info("product_lookup", query=query)

        try:
            # Try USDA first if it's a UPC
            if query.isdigit() and len(query) >= 12:
                result = self._lookup_by_upc(query)
            else:
                result = self._lookup_by_name(query)

            if result:
                return self._format_result(result)
            else:
                return f"No product information found for: {query}"

        except Exception as e:
            logger.error("product_lookup_failed", error=str(e))
            return f"Error looking up product: {str(e)}"

    async def arun(self, query: str) -> str:
        """Async execution - wraps sync version for now."""
        return self.run(query)

    def _lookup_by_upc(self, upc: str) -> Optional[Dict[str, Any]]:
        """
        Look up product by UPC code.

        Args:
            upc: UPC code

        Returns:
            Product information dict or None
        """
        # Placeholder - would call actual APIs
        logger.info("upc_lookup", upc=upc)
        return None

    def _lookup_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        """
        Look up product by name.

        Args:
            name: Product name

        Returns:
            Product information dict or None
        """
        # Placeholder - would call actual APIs
        logger.info("name_lookup", name=name)
        return None

    def _format_result(self, result: Dict[str, Any]) -> str:
        """
        Format product lookup result.

        Args:
            result: Product information dict

        Returns:
            Formatted string
        """
        parts = ["Product Information:\n"]

        if "name" in result:
            parts.append(f"Name: {result['name']}")
        if "brand" in result:
            parts.append(f"Brand: {result['brand']}")
        if "category" in result:
            parts.append(f"Category: {result['category']}")
        if "ingredients" in result:
            parts.append(f"Ingredients: {result['ingredients']}")
        if "nutrition_label_type" in result:
            parts.append(f"Label Type: {result['nutrition_label_type']}")

        return "\n".join(parts)
