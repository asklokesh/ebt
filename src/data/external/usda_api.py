"""USDA FoodData Central API client."""

from typing import Any, Dict, List, Optional

import httpx

from src.core.config import settings
from src.core.exceptions import ExternalAPIError
from src.utils.logging import get_logger

logger = get_logger(__name__)


class USDAFoodDataClient:
    """
    Client for USDA FoodData Central API.

    API Documentation: https://fdc.nal.usda.gov/api-guide.html
    """

    BASE_URL = "https://api.nal.usda.gov/fdc/v1"

    def __init__(self, api_key: str = None):
        """
        Initialize the USDA API client.

        Args:
            api_key: USDA API key (optional, uses settings if not provided)
        """
        self.api_key = api_key or settings.usda_api_key
        self._client = None

    @property
    def client(self) -> httpx.AsyncClient:
        """Get or create async HTTP client."""
        if self._client is None:
            self._client = httpx.AsyncClient(
                base_url=self.BASE_URL,
                timeout=30.0,
            )
        return self._client

    def is_configured(self) -> bool:
        """Check if API key is configured."""
        return self.api_key is not None and len(self.api_key) > 0

    async def search_foods(
        self,
        query: str,
        page_size: int = 10,
        data_type: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Search for foods in the FoodData Central database.

        Args:
            query: Search query
            page_size: Number of results to return
            data_type: Filter by data type (e.g., ["Branded", "Survey (FNDDS)"])

        Returns:
            Search results dict
        """
        if not self.is_configured():
            logger.warning("usda_api_not_configured")
            return {"foods": [], "total": 0}

        try:
            params = {
                "api_key": self.api_key,
                "query": query,
                "pageSize": page_size,
            }

            if data_type:
                params["dataType"] = data_type

            response = await self.client.get("/foods/search", params=params)
            response.raise_for_status()

            data = response.json()
            logger.info(
                "usda_search_completed",
                query=query,
                results=len(data.get("foods", [])),
            )

            return data

        except httpx.HTTPStatusError as e:
            logger.error(
                "usda_api_error",
                status_code=e.response.status_code,
                query=query,
            )
            raise ExternalAPIError(
                message=f"USDA API error: {e.response.status_code}",
                api_name="USDA FoodData Central",
                status_code=e.response.status_code,
            )
        except Exception as e:
            logger.error("usda_api_error", error=str(e))
            raise ExternalAPIError(
                message=f"USDA API error: {e}",
                api_name="USDA FoodData Central",
            )

    async def get_food(self, fdc_id: int) -> Optional[Dict[str, Any]]:
        """
        Get detailed information about a specific food.

        Args:
            fdc_id: FoodData Central ID

        Returns:
            Food details dict or None
        """
        if not self.is_configured():
            logger.warning("usda_api_not_configured")
            return None

        try:
            params = {"api_key": self.api_key}

            response = await self.client.get(f"/food/{fdc_id}", params=params)
            response.raise_for_status()

            data = response.json()
            logger.info("usda_food_retrieved", fdc_id=fdc_id)

            return data

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                return None
            raise ExternalAPIError(
                message=f"USDA API error: {e.response.status_code}",
                api_name="USDA FoodData Central",
                status_code=e.response.status_code,
            )
        except Exception as e:
            logger.error("usda_api_error", error=str(e))
            raise ExternalAPIError(
                message=f"USDA API error: {e}",
                api_name="USDA FoodData Central",
            )

    async def search_by_upc(self, upc: str) -> Optional[Dict[str, Any]]:
        """
        Search for a food by UPC/GTIN code.

        Args:
            upc: UPC or GTIN code

        Returns:
            Food details dict or None
        """
        if not self.is_configured():
            return None

        # Search with UPC as query, filter to branded foods
        results = await self.search_foods(
            query=upc,
            page_size=5,
            data_type=["Branded"],
        )

        foods = results.get("foods", [])

        # Look for exact UPC match
        for food in foods:
            if food.get("gtinUpc") == upc:
                return food

        # Return first result if no exact match
        return foods[0] if foods else None

    def extract_product_info(self, food_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract relevant product information from USDA API response.

        Args:
            food_data: Raw food data from API

        Returns:
            Extracted product information
        """
        return {
            "fdc_id": food_data.get("fdcId"),
            "description": food_data.get("description"),
            "brand_owner": food_data.get("brandOwner"),
            "brand_name": food_data.get("brandName"),
            "ingredients": food_data.get("ingredients"),
            "serving_size": food_data.get("servingSize"),
            "serving_size_unit": food_data.get("servingSizeUnit"),
            "food_category": food_data.get("foodCategory"),
            "data_type": food_data.get("dataType"),
            "gtin_upc": food_data.get("gtinUpc"),
        }

    async def close(self) -> None:
        """Close the HTTP client."""
        if self._client:
            await self._client.aclose()
            self._client = None


# Global client instance
_client: USDAFoodDataClient | None = None


def get_usda_client() -> USDAFoodDataClient:
    """Get the global USDA API client."""
    global _client
    if _client is None:
        _client = USDAFoodDataClient()
    return _client
