"""Product search routes."""

import json
import re
from typing import List, Optional

from fastapi import APIRouter, Query
from pydantic import BaseModel

from src.core.config import settings
from src.data.external.usda_api import get_usda_client
from src.services.pricing import search_product_prices, PriceInfo
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
    # Pricing fields
    avg_price: Optional[float] = None
    min_price: Optional[float] = None
    max_price: Optional[float] = None
    price_currency: str = "USD"
    price_source: Optional[str] = None


class SearchResponse(BaseModel):
    """Search response with product suggestions."""

    query: str
    results: List[ProductSuggestion]
    total: int
    source: str
    has_pricing: bool = False


@router.get("/products", response_model=SearchResponse)
async def search_products(
    q: str = Query(..., min_length=2, description="Search query"),
    limit: int = Query(default=10, ge=1, le=50, description="Max results"),
    include_prices: bool = Query(default=True, description="Include pricing data"),
) -> SearchResponse:
    """
    Search for products by name or UPC.

    Returns product suggestions from USDA FoodData Central or LLM,
    with optional pricing data from Open Prices API.
    """
    logger.info("product_search", query=q, limit=limit, include_prices=include_prices)

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

    # Check if LLM already provided prices
    has_pricing = any(r.avg_price is not None for r in results)

    # If no LLM prices, try Open Prices API
    if include_prices and results and not has_pricing:
        has_pricing = await _enrich_with_prices(q, results)

    return SearchResponse(
        query=q,
        results=results[:limit],
        total=len(results),
        source="usda" if usda_client.is_configured() and results else "llm",
        has_pricing=has_pricing,
    )


async def _enrich_with_prices(query: str, results: List[ProductSuggestion]) -> bool:
    """
    Enrich product results with pricing data from Open Prices API.

    Returns True if any pricing data was found.
    """
    try:
        price_data = await search_product_prices(query, limit=len(results) * 2)

        if not price_data:
            return False

        # Create lookup by normalized product name
        price_lookup = {}
        for p in price_data:
            key = p.product_name.lower().strip()
            price_lookup[key] = p
            # Also index by first few words for fuzzy matching
            words = key.split()[:3]
            if len(words) >= 2:
                price_lookup[" ".join(words)] = p

        # Match prices to products
        matched = 0
        for result in results:
            result_name = result.name.lower().strip()

            # Try exact match first
            if result_name in price_lookup:
                price_info = price_lookup[result_name]
                result.avg_price = price_info.avg_price
                result.min_price = price_info.min_price
                result.max_price = price_info.max_price
                result.price_source = "Open Prices"
                matched += 1
                continue

            # Try partial match
            result_words = result_name.split()[:3]
            if len(result_words) >= 2:
                partial_key = " ".join(result_words)
                if partial_key in price_lookup:
                    price_info = price_lookup[partial_key]
                    result.avg_price = price_info.avg_price
                    result.min_price = price_info.min_price
                    result.max_price = price_info.max_price
                    result.price_source = "Open Prices"
                    matched += 1

        logger.info("prices_matched", matched=matched, total=len(results))
        return matched > 0

    except Exception as e:
        logger.warning("price_enrichment_failed", error=str(e))
        return False


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
- typical_price: Typical US retail price in dollars (number only, e.g., 4.99)

Return ONLY valid JSON array, no other text. Example format:
[{{"name": "Horizon Organic Whole Milk", "brand": "Horizon", "category": "Dairy", "typical_price": 5.99}}]

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
                    # Extract price from LLM response
                    typical_price = p.get("typical_price")
                    if typical_price is not None:
                        try:
                            typical_price = float(typical_price)
                        except (ValueError, TypeError):
                            typical_price = None

                    results.append(ProductSuggestion(
                        name=p.get("name", "Unknown"),
                        brand=p.get("brand"),
                        category=p.get("category"),
                        data_source="llm",
                        avg_price=typical_price,
                        min_price=typical_price,
                        max_price=typical_price,
                        price_source="LLM Estimate" if typical_price else None,
                    ))

            logger.info("llm_search_success", results=len(results))
            return results

    except json.JSONDecodeError as e:
        logger.warning("llm_json_parse_failed", error=str(e))
    except Exception as e:
        logger.warning("llm_search_failed", error=str(e))

    return []
