"""SNAP guidelines fetcher and parser."""

import re
from typing import List, Optional

import httpx

from src.core.exceptions import ExternalAPIError
from src.utils.logging import get_logger

logger = get_logger(__name__)


class SNAPGuidelinesFetcher:
    """
    Fetches and parses SNAP eligibility guidelines from official sources.

    Sources:
    - FNS Eligible Food Items: https://www.fns.usda.gov/snap/eligible-food-items
    - 7 CFR 271.2: https://www.ecfr.gov/current/title-7/section-271.2
    """

    SOURCES = {
        "fns_eligible": {
            "url": "https://www.fns.usda.gov/snap/eligible-food-items",
            "name": "FNS Eligible Food Items",
        },
        "ecfr_271_2": {
            "url": "https://www.ecfr.gov/current/title-7/section-271.2",
            "name": "7 CFR 271.2 - SNAP Definitions",
        },
    }

    def __init__(self):
        """Initialize the guidelines fetcher."""
        self._client = None

    @property
    def client(self) -> httpx.AsyncClient:
        """Get or create async HTTP client."""
        if self._client is None:
            self._client = httpx.AsyncClient(
                timeout=60.0,
                follow_redirects=True,
                headers={
                    "User-Agent": "Mozilla/5.0 (compatible; EBTClassifier/1.0)",
                },
            )
        return self._client

    async def fetch_page(self, url: str) -> Optional[str]:
        """
        Fetch a web page.

        Args:
            url: URL to fetch

        Returns:
            Page content as string or None
        """
        try:
            response = await self.client.get(url)
            response.raise_for_status()

            logger.info("page_fetched", url=url, status=response.status_code)
            return response.text

        except httpx.HTTPStatusError as e:
            logger.error(
                "fetch_error",
                url=url,
                status_code=e.response.status_code,
            )
            return None
        except Exception as e:
            logger.error("fetch_error", url=url, error=str(e))
            return None

    def extract_text_from_html(self, html: str) -> str:
        """
        Extract clean text from HTML content.

        Args:
            html: Raw HTML content

        Returns:
            Extracted text
        """
        # Remove script and style elements
        html = re.sub(r"<script[^>]*>.*?</script>", "", html, flags=re.DOTALL | re.IGNORECASE)
        html = re.sub(r"<style[^>]*>.*?</style>", "", html, flags=re.DOTALL | re.IGNORECASE)

        # Remove HTML comments
        html = re.sub(r"<!--.*?-->", "", html, flags=re.DOTALL)

        # Remove HTML tags
        text = re.sub(r"<[^>]+>", " ", html)

        # Decode HTML entities
        text = text.replace("&nbsp;", " ")
        text = text.replace("&amp;", "&")
        text = text.replace("&lt;", "<")
        text = text.replace("&gt;", ">")
        text = text.replace("&quot;", '"')

        # Normalize whitespace
        text = re.sub(r"\s+", " ", text)
        text = "\n".join(line.strip() for line in text.split("\n") if line.strip())

        return text.strip()

    async def fetch_and_parse(self, source_key: str) -> Optional[str]:
        """
        Fetch and parse a guideline source.

        Args:
            source_key: Key from SOURCES dict

        Returns:
            Parsed text content or None
        """
        if source_key not in self.SOURCES:
            logger.error("unknown_source", source_key=source_key)
            return None

        source = self.SOURCES[source_key]
        html = await self.fetch_page(source["url"])

        if not html:
            return None

        text = self.extract_text_from_html(html)

        logger.info(
            "guidelines_parsed",
            source=source["name"],
            length=len(text),
        )

        return text

    async def fetch_all_guidelines(self) -> dict[str, str]:
        """
        Fetch all guideline sources.

        Returns:
            Dict mapping source keys to parsed content
        """
        results = {}

        for key in self.SOURCES:
            content = await self.fetch_and_parse(key)
            if content:
                results[key] = content

        return results

    def get_embedded_guidelines(self) -> dict[str, str]:
        """
        Get embedded guideline summaries (for offline use).

        Returns:
            Dict mapping source keys to embedded content
        """
        return {
            "eligible_summary": """
SNAP Eligible Food Items Summary:

SNAP benefits can be used to buy:
- Breads and cereals
- Fruits and vegetables
- Meats, fish, and poultry
- Dairy products
- Seeds and plants to grow food

Foods with Nutrition Facts labels are generally eligible if they are:
- Intended for human consumption
- Not hot at point of sale
- Not for on-premises consumption
- Not alcoholic beverages
- Not tobacco products
            """.strip(),
            "ineligible_summary": """
SNAP Ineligible Items Summary:

SNAP benefits CANNOT be used to buy:
- Alcoholic beverages (beer, wine, liquor)
- Tobacco products (cigarettes, cigars, vapes)
- Vitamins and supplements (items with Supplement Facts labels)
- Medicines
- Hot foods ready to eat
- Foods for on-premises consumption (restaurant meals)
- Non-food items (pet food, cleaning supplies)
- Live animals (except certain shellfish)
- CBD and cannabis products
            """.strip(),
        }

    async def close(self) -> None:
        """Close the HTTP client."""
        if self._client:
            await self._client.aclose()
            self._client = None


# Global fetcher instance
_fetcher: SNAPGuidelinesFetcher | None = None


def get_snap_guidelines_fetcher() -> SNAPGuidelinesFetcher:
    """Get the global SNAP guidelines fetcher."""
    global _fetcher
    if _fetcher is None:
        _fetcher = SNAPGuidelinesFetcher()
    return _fetcher
