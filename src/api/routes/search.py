"""Product search routes."""

from typing import List, Optional

from fastapi import APIRouter, Query
from pydantic import BaseModel

from src.data.external.usda_api import get_usda_client
from src.utils.logging import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/search", tags=["search"])


class ProductSuggestion(BaseModel):
    """A product suggestion from search."""

    name: str
    brand: Optional[str] = None
    category: Optional[str] = None
    upc: Optional[str] = None
    description: Optional[str] = None
    ingredients: Optional[str] = None
    fdc_id: Optional[int] = None
    data_source: str = "usda"


class SearchResponse(BaseModel):
    """Search response with product suggestions."""

    query: str
    results: List[ProductSuggestion]
    total: int
    source: str


@router.get("/products", response_model=SearchResponse)
async def search_products(
    q: str = Query(..., min_length=2, description="Search query"),
    limit: int = Query(default=10, ge=1, le=50, description="Max results"),
) -> SearchResponse:
    """
    Search for products by name or UPC.

    Returns product suggestions from USDA FoodData Central database.
    """
    logger.info("product_search", query=q, limit=limit)

    usda_client = get_usda_client()
    results: List[ProductSuggestion] = []

    # Try USDA search if configured
    if usda_client.is_configured():
        try:
            usda_results = await usda_client.search_foods(
                query=q,
                page_size=limit,
            )

            for food in usda_results.get("foods", []):
                results.append(ProductSuggestion(
                    name=food.get("description", "Unknown"),
                    brand=food.get("brandOwner") or food.get("brandName"),
                    category=food.get("foodCategory"),
                    upc=food.get("gtinUpc"),
                    description=food.get("additionalDescriptions"),
                    ingredients=food.get("ingredients"),
                    fdc_id=food.get("fdcId"),
                    data_source="usda",
                ))

            logger.info("usda_search_success", results=len(results))

        except Exception as e:
            logger.warning("usda_search_failed", error=str(e))

    # If no USDA results, provide common products as fallback
    if not results:
        results = _get_common_products(q, limit)

    return SearchResponse(
        query=q,
        results=results[:limit],
        total=len(results),
        source="usda" if usda_client.is_configured() else "fallback",
    )


def _get_common_products(query: str, limit: int) -> List[ProductSuggestion]:
    """
    Get common products matching query as fallback.

    This provides basic functionality when USDA API is not configured.
    """
    query_lower = query.lower()

    # Common products database (fallback)
    common_products = [
        ProductSuggestion(name="Fresh Apples", category="Produce", data_source="fallback"),
        ProductSuggestion(name="Organic Bananas", category="Produce", data_source="fallback"),
        ProductSuggestion(name="Whole Milk", brand="Dairy Pure", category="Dairy", data_source="fallback"),
        ProductSuggestion(name="2% Reduced Fat Milk", category="Dairy", data_source="fallback"),
        ProductSuggestion(name="White Bread", brand="Wonder", category="Bakery", data_source="fallback"),
        ProductSuggestion(name="Whole Wheat Bread", category="Bakery", data_source="fallback"),
        ProductSuggestion(name="Ground Beef 80/20", category="Meat", data_source="fallback"),
        ProductSuggestion(name="Chicken Breast", category="Meat", data_source="fallback"),
        ProductSuggestion(name="Eggs Large Grade A", category="Dairy", data_source="fallback"),
        ProductSuggestion(name="Cheddar Cheese", category="Dairy", data_source="fallback"),
        ProductSuggestion(name="Orange Juice", brand="Tropicana", category="Beverages", data_source="fallback"),
        ProductSuggestion(name="Coca-Cola", brand="Coca-Cola", category="Beverages", data_source="fallback"),
        ProductSuggestion(name="Pepsi Cola", brand="PepsiCo", category="Beverages", data_source="fallback"),
        ProductSuggestion(name="Monster Energy Drink", brand="Monster", category="Beverages", data_source="fallback"),
        ProductSuggestion(name="Red Bull Energy Drink", brand="Red Bull", category="Beverages", data_source="fallback"),
        ProductSuggestion(name="Budweiser Beer", brand="Anheuser-Busch", category="Alcohol", data_source="fallback"),
        ProductSuggestion(name="Corona Extra Beer", brand="Corona", category="Alcohol", data_source="fallback"),
        ProductSuggestion(name="Jack Daniel's Whiskey", brand="Jack Daniel's", category="Alcohol", data_source="fallback"),
        ProductSuggestion(name="Marlboro Cigarettes", brand="Philip Morris", category="Tobacco", data_source="fallback"),
        ProductSuggestion(name="Centrum Multivitamin", brand="Centrum", category="Supplements", data_source="fallback"),
        ProductSuggestion(name="Vitamin D3 Supplement", category="Supplements", data_source="fallback"),
        ProductSuggestion(name="Fish Oil Omega-3", category="Supplements", data_source="fallback"),
        ProductSuggestion(name="Rotisserie Chicken (Hot)", category="Prepared Foods", data_source="fallback"),
        ProductSuggestion(name="Hot Dog (Ready to Eat)", category="Prepared Foods", data_source="fallback"),
        ProductSuggestion(name="Pizza Slice (Hot)", category="Prepared Foods", data_source="fallback"),
        ProductSuggestion(name="Frozen Pizza", brand="DiGiorno", category="Frozen Foods", data_source="fallback"),
        ProductSuggestion(name="Ice Cream", brand="Ben & Jerry's", category="Frozen Foods", data_source="fallback"),
        ProductSuggestion(name="Potato Chips", brand="Lay's", category="Snacks", data_source="fallback"),
        ProductSuggestion(name="Doritos", brand="Frito-Lay", category="Snacks", data_source="fallback"),
        ProductSuggestion(name="Oreo Cookies", brand="Nabisco", category="Snacks", data_source="fallback"),
        ProductSuggestion(name="Baby Formula", brand="Similac", category="Baby Food", data_source="fallback"),
        ProductSuggestion(name="Gerber Baby Food", brand="Gerber", category="Baby Food", data_source="fallback"),
        ProductSuggestion(name="Canned Tomatoes", brand="Hunt's", category="Canned Goods", data_source="fallback"),
        ProductSuggestion(name="Canned Beans", category="Canned Goods", data_source="fallback"),
        ProductSuggestion(name="Vegetable Seeds", category="Seeds", data_source="fallback"),
        ProductSuggestion(name="CBD Gummies", category="CBD Products", data_source="fallback"),
    ]

    # Filter by query
    matching = [
        p for p in common_products
        if query_lower in p.name.lower() or
           (p.brand and query_lower in p.brand.lower()) or
           (p.category and query_lower in p.category.lower())
    ]

    return matching[:limit] if matching else common_products[:limit]
