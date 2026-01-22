"""Product search routes."""

import json
import re
from typing import List, Optional

from fastapi import APIRouter, Query
from pydantic import BaseModel

from src.core.config import settings
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

    Returns product suggestions from USDA FoodData Central or LLM.
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

    # If no USDA results, use LLM to suggest products
    if not results:
        results = await _get_llm_suggestions(q, limit)

    return SearchResponse(
        query=q,
        results=results[:limit],
        total=len(results),
        source="usda" if usda_client.is_configured() and results else "llm",
    )


async def _get_llm_suggestions(query: str, limit: int) -> List[ProductSuggestion]:
    """
    Use LLM to suggest products matching the query.
    """
    if not settings.ollama_enabled:
        logger.warning("llm_not_configured_for_search")
        return []

    try:
        from langchain_ollama import ChatOllama

        llm = ChatOllama(
            model=settings.ollama_model,
            base_url=settings.ollama_base_url,
            temperature=0.3,
        )

        prompt = f"""You are a product database assistant. Given a search query, suggest real grocery/food products that match.

Search query: "{query}"

Return exactly {limit} products as a JSON array. Each product should have:
- name: Full product name (be specific, e.g., "Horizon Organic Whole Milk" not just "Milk")
- brand: Brand name if applicable (e.g., "Horizon", "Tropicana", "Lay's")
- category: One of: Produce, Dairy, Meat, Seafood, Bakery, Beverages, Snacks, Frozen Foods, Canned Goods, Condiments, Baby Food, Supplements, Alcohol, Tobacco, Prepared Foods, Other

Return ONLY valid JSON array, no other text. Example format:
[{{"name": "Horizon Organic Whole Milk", "brand": "Horizon", "category": "Dairy"}}]

Products matching "{query}":"""

        response = await llm.ainvoke(prompt)
        content = response.content.strip()

        # Extract JSON from response
        json_match = re.search(r'\[.*\]', content, re.DOTALL)
        if json_match:
            products_data = json.loads(json_match.group())

            results = []
            for p in products_data[:limit]:
                if isinstance(p, dict) and p.get("name"):
                    results.append(ProductSuggestion(
                        name=p.get("name", "Unknown"),
                        brand=p.get("brand"),
                        category=p.get("category"),
                        data_source="llm",
                    ))

            logger.info("llm_search_success", results=len(results))
            return results

    except json.JSONDecodeError as e:
        logger.warning("llm_json_parse_failed", error=str(e))
    except Exception as e:
        logger.warning("llm_search_failed", error=str(e))

    return []
