"""Open Food Facts API client."""

from typing import Any, Dict, Optional

import httpx

from src.core.exceptions import ExternalAPIError
from src.utils.logging import get_logger

logger = get_logger(__name__)


class OpenFoodFactsClient:
    """
    Client for Open Food Facts API.

    API Documentation: https://wiki.openfoodfacts.org/API
    """

    BASE_URL = "https://world.openfoodfacts.org/api/v2"
    USER_AGENT = "EBTClassifier/1.0 (contact@example.com)"

    def __init__(self):
        """Initialize the Open Food Facts client."""
        self._client = None

    @property
    def client(self) -> httpx.AsyncClient:
        """Get or create async HTTP client."""
        if self._client is None:
            self._client = httpx.AsyncClient(
                base_url=self.BASE_URL,
                timeout=30.0,
                headers={"User-Agent": self.USER_AGENT},
            )
        return self._client

    async def get_product_by_barcode(
        self,
        barcode: str,
    ) -> Optional[Dict[str, Any]]:
        """
        Get product information by barcode.

        Args:
            barcode: Product barcode (UPC, EAN, etc.)

        Returns:
            Product data dict or None
        """
        try:
            response = await self.client.get(f"/product/{barcode}.json")
            response.raise_for_status()

            data = response.json()

            if data.get("status") == 0:
                logger.info("openfoodfacts_product_not_found", barcode=barcode)
                return None

            product = data.get("product", {})
            logger.info(
                "openfoodfacts_product_found",
                barcode=barcode,
                name=product.get("product_name"),
            )

            return product

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                return None
            logger.error(
                "openfoodfacts_api_error",
                status_code=e.response.status_code,
                barcode=barcode,
            )
            raise ExternalAPIError(
                message=f"Open Food Facts API error: {e.response.status_code}",
                api_name="Open Food Facts",
                status_code=e.response.status_code,
            )
        except Exception as e:
            logger.error("openfoodfacts_api_error", error=str(e))
            raise ExternalAPIError(
                message=f"Open Food Facts API error: {e}",
                api_name="Open Food Facts",
            )

    async def search_products(
        self,
        query: str,
        page_size: int = 10,
        categories: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Search for products.

        Args:
            query: Search query
            page_size: Number of results per page
            categories: Filter by categories

        Returns:
            Search results dict
        """
        try:
            params = {
                "search_terms": query,
                "page_size": page_size,
                "json": "true",
            }

            if categories:
                params["categories_tags"] = categories

            response = await self.client.get("/search", params=params)
            response.raise_for_status()

            data = response.json()
            logger.info(
                "openfoodfacts_search_completed",
                query=query,
                count=data.get("count", 0),
            )

            return data

        except Exception as e:
            logger.error("openfoodfacts_search_error", error=str(e))
            raise ExternalAPIError(
                message=f"Open Food Facts search error: {e}",
                api_name="Open Food Facts",
            )

    def extract_product_info(self, product_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract relevant product information from Open Food Facts response.

        Args:
            product_data: Raw product data from API

        Returns:
            Extracted product information
        """
        # Extract ingredients as list
        ingredients_text = product_data.get("ingredients_text", "")
        ingredients = [
            i.strip()
            for i in ingredients_text.split(",")
            if i.strip()
        ] if ingredients_text else []

        # Determine nutrition label type based on categories
        categories = product_data.get("categories_tags", [])
        nutrition_label_type = "nutrition_facts"
        if any("supplement" in cat.lower() for cat in categories):
            nutrition_label_type = "supplement_facts"
        elif any("vitamin" in cat.lower() for cat in categories):
            nutrition_label_type = "supplement_facts"

        # Check for alcohol
        alcohol_value = product_data.get("alcohol_value")
        alcohol_content = None
        if alcohol_value is not None:
            try:
                alcohol_content = float(alcohol_value) / 100  # Convert to decimal
            except (ValueError, TypeError):
                pass

        return {
            "barcode": product_data.get("code"),
            "product_name": product_data.get("product_name"),
            "brand": product_data.get("brands"),
            "categories": product_data.get("categories"),
            "category_tags": categories,
            "ingredients": ingredients,
            "ingredients_text": ingredients_text,
            "nutrition_label_type": nutrition_label_type,
            "alcohol_content": alcohol_content,
            "image_url": product_data.get("image_url"),
            "nutriscore_grade": product_data.get("nutriscore_grade"),
            "nova_group": product_data.get("nova_group"),
        }

    async def close(self) -> None:
        """Close the HTTP client."""
        if self._client:
            await self._client.aclose()
            self._client = None


# Global client instance
_client: OpenFoodFactsClient | None = None


def get_openfoodfacts_client() -> OpenFoodFactsClient:
    """Get the global Open Food Facts client."""
    global _client
    if _client is None:
        _client = OpenFoodFactsClient()
    return _client
