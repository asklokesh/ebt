"""
Pricing service using Open Food Facts Open Prices API.
https://prices.openfoodfacts.org/
"""

import httpx
from typing import Optional, List
from pydantic import BaseModel
from src.utils.logging import get_logger

logger = get_logger(__name__)

OPEN_PRICES_BASE_URL = "https://prices.openfoodfacts.org/api/v1"


class PriceInfo(BaseModel):
    """Price information for a product."""
    price: float
    currency: Optional[str] = "USD"
    store_name: Optional[str] = None
    store_location: Optional[str] = None
    date: Optional[str] = None
    source: str = "Open Prices"


class ProductPrice(BaseModel):
    """Product with price information."""
    product_name: str
    brand: Optional[str] = None
    barcode: Optional[str] = None
    prices: List[PriceInfo] = []
    avg_price: Optional[float] = None
    min_price: Optional[float] = None
    max_price: Optional[float] = None


async def search_product_prices(
    query: str,
    limit: int = 5,
) -> List[ProductPrice]:
    """
    Search for product prices using Open Prices API.

    Args:
        query: Product name to search
        limit: Maximum number of results

    Returns:
        List of products with price information
    """
    results = []

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            # Search for prices by product name
            response = await client.get(
                f"{OPEN_PRICES_BASE_URL}/prices",
                params={
                    "product_name__like": f"%{query}%",
                    "size": limit * 5,  # Get more to aggregate
                    "order_by": "-date",
                }
            )

            if response.status_code != 200:
                logger.warning("open_prices_api_error", status=response.status_code)
                return []

            data = response.json()
            items = data.get("items", [])

            # Filter items that have prices (some are price tags without values)
            items = [item for item in items if item.get("price") is not None]

            if not items:
                logger.info("no_prices_found", query=query)
                return []

            # Aggregate prices by product
            product_prices = {}
            for item in items:
                product_name = item.get("product_name") or item.get("product", {}).get("product_name")
                if not product_name:
                    continue

                price = item.get("price")
                if price is None:
                    continue

                # Use product name as key for aggregation
                key = product_name.lower().strip()

                if key not in product_prices:
                    product_prices[key] = {
                        "product_name": product_name,
                        "brand": item.get("product", {}).get("brands"),
                        "barcode": item.get("product_code"),
                        "prices": [],
                    }

                # Get location info
                location = item.get("location", {})
                store_name = location.get("osm_name") or location.get("name")

                product_prices[key]["prices"].append(
                    PriceInfo(
                        price=float(price),
                        currency=item.get("currency") or "USD",
                        store_name=store_name,
                        store_location=location.get("osm_address_city"),
                        date=item.get("date"),
                    )
                )

            # Calculate stats and build results
            for key, prod_data in list(product_prices.items())[:limit]:
                prices = prod_data["prices"]
                price_values = [p.price for p in prices]

                results.append(ProductPrice(
                    product_name=prod_data["product_name"],
                    brand=prod_data["brand"],
                    barcode=prod_data["barcode"],
                    prices=prices[:3],  # Keep top 3 recent prices
                    avg_price=round(sum(price_values) / len(price_values), 2) if price_values else None,
                    min_price=min(price_values) if price_values else None,
                    max_price=max(price_values) if price_values else None,
                ))

            logger.info("prices_fetched", query=query, count=len(results))

    except httpx.TimeoutException:
        logger.warning("open_prices_timeout", query=query)
    except Exception as e:
        logger.error("open_prices_error", error=str(e), query=query)

    return results


async def get_price_by_barcode(barcode: str) -> Optional[ProductPrice]:
    """
    Get price information for a product by barcode.

    Args:
        barcode: Product barcode/UPC

    Returns:
        Product with price information or None
    """
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                f"{OPEN_PRICES_BASE_URL}/prices",
                params={
                    "product_code": barcode,
                    "size": 10,
                    "order_by": "-date",
                }
            )

            if response.status_code != 200:
                return None

            data = response.json()
            items = data.get("items", [])

            if not items:
                return None

            # Aggregate all prices for this barcode
            prices = []
            product_name = None
            brand = None

            for item in items:
                if not product_name:
                    product_name = item.get("product_name") or item.get("product", {}).get("product_name")
                    brand = item.get("product", {}).get("brands")

                price = item.get("price")
                if price is not None:
                    location = item.get("location", {})
                    prices.append(PriceInfo(
                        price=float(price),
                        currency=item.get("currency") or "USD",
                        store_name=location.get("osm_name") or location.get("name"),
                        store_location=location.get("osm_address_city"),
                        date=item.get("date"),
                    ))

            if not prices:
                return None

            price_values = [p.price for p in prices]

            return ProductPrice(
                product_name=product_name or "Unknown",
                brand=brand,
                barcode=barcode,
                prices=prices[:5],
                avg_price=round(sum(price_values) / len(price_values), 2),
                min_price=min(price_values),
                max_price=max(price_values),
            )

    except Exception as e:
        logger.error("barcode_price_error", error=str(e), barcode=barcode)
        return None
