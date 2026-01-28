"""EBT Eligibility Check - Clean, minimal design with saved list feature."""

import streamlit as st
import httpx
import os
import json
import re
import base64
from typing import Optional, Dict, Any, List

# API URL from environment or default
API_URL = os.environ.get("API_URL", "http://localhost:8000")

# Kroger API configuration (Certification environment)
KROGER_TOKEN_URL = "https://api-ce.kroger.com/v1/connect/oauth2/token"
KROGER_PRODUCT_URL = "https://api-ce.kroger.com/v1/products"
KROGER_LOCATION_URL = "https://api-ce.kroger.com/v1/locations"

# Check if we're running on Streamlit Cloud (no local API)
IS_CLOUD = os.environ.get("STREAMLIT_SHARING_MODE") or not os.environ.get("API_URL")

# Design tokens
COLORS = {
    "accent": "#D4A27C",
    "success": "#10A37F",
    "error": "#EF4444",
    "bg": "#FAFAF9",
    "card": "#FFFFFF",
    "text": "#1A1A1A",
    "muted": "#6B7280",
}


def inject_styles():
    """Inject custom CSS for clean design."""
    st.markdown(f"""
    <style>
        /* Page background */
        .stApp {{
            background-color: {COLORS['bg']};
        }}

        /* Search input styling */
        .stTextInput > div > div > input {{
            border-radius: 12px;
            border: 1px solid #E5E5E5;
            padding: 16px 20px;
            font-size: 16px;
            background: white;
        }}
        .stTextInput > div > div > input:focus {{
            border-color: {COLORS['accent']};
            box-shadow: 0 0 0 2px rgba(212, 162, 124, 0.2);
        }}

        /* Result badges */
        .result-badge {{
            display: inline-flex;
            align-items: center;
            gap: 8px;
            padding: 12px 24px;
            border-radius: 8px;
            font-weight: 600;
            font-size: 18px;
        }}
        .result-eligible {{
            background: rgba(16, 163, 127, 0.1);
            color: {COLORS['success']};
        }}
        .result-ineligible {{
            background: rgba(239, 68, 68, 0.1);
            color: {COLORS['error']};
        }}

        /* Saved list item */
        .saved-item {{
            background: white;
            border-radius: 8px;
            padding: 12px 16px;
            margin: 4px 0;
            border: 1px solid #E5E5E5;
        }}

        /* Hide default streamlit elements */
        #MainMenu {{visibility: hidden;}}
        footer {{visibility: hidden;}}

        /* Button styling */
        .stButton > button {{
            border-radius: 8px;
            font-weight: 500;
            padding: 8px 16px;
        }}

        /* Section headers */
        .section-header {{
            font-size: 14px;
            font-weight: 600;
            color: {COLORS['muted']};
            text-transform: uppercase;
            letter-spacing: 0.05em;
            margin-bottom: 12px;
        }}

        /* List badge */
        .list-count {{
            background: {COLORS['accent']};
            color: white;
            padding: 2px 8px;
            border-radius: 12px;
            font-size: 12px;
            font-weight: 600;
        }}
    </style>
    """, unsafe_allow_html=True)


def get_llm_headers() -> dict:
    """Get headers for LLM mode from session state."""
    headers = {}
    if st.session_state.get("llm_mode") == "cloud" and st.session_state.get("ollama_cloud_key"):
        headers["X-Ollama-Mode"] = "cloud"
        headers["X-Ollama-Cloud-Key"] = st.session_state.ollama_cloud_key
    return headers


def get_cloud_llm():
    """Get Ollama Cloud client for direct calls."""
    api_key = st.session_state.get("ollama_cloud_key", "")
    if not api_key:
        return None

    base_url = st.session_state.get("ollama_cloud_base_url", "https://ollama.com")
    model = st.session_state.get("ollama_cloud_model", "glm-4.7:cloud")

    try:
        import ollama
        client = ollama.Client(
            host=base_url,
            headers={"Authorization": f"Bearer {api_key}"}
        )
        return {"client": client, "model": model}
    except Exception as e:
        st.error(f"Failed to initialize Ollama Cloud: {e}")
        return None


def call_cloud_llm(prompt: str) -> str:
    """Call Ollama Cloud with a prompt and return the response."""
    llm_config = get_cloud_llm()
    if not llm_config:
        return None

    try:
        response = llm_config["client"].chat(
            model=llm_config["model"],
            messages=[{"role": "user", "content": prompt}]
        )
        return response["message"]["content"]
    except Exception as e:
        st.error(f"LLM call failed: {e}")
        return None


def get_kroger_token() -> Optional[str]:
    """Get Kroger API access token using client credentials."""
    try:
        client_id = st.secrets.get("KROGER_CLIENT_ID", "")
        client_secret = st.secrets.get("KROGER_CLIENT_SECRET", "")

        if not client_id or not client_secret:
            return None

        # Check if we have a cached token
        if "kroger_token" in st.session_state:
            token_data = st.session_state.kroger_token
            # Simple expiry check (tokens last 30 min, refresh after 25)
            import time
            if token_data.get("expires_at", 0) > time.time():
                return token_data.get("access_token")

        # Get new token
        credentials = base64.b64encode(f"{client_id}:{client_secret}".encode()).decode()

        response = httpx.post(
            KROGER_TOKEN_URL,
            headers={
                "Content-Type": "application/x-www-form-urlencoded",
                "Authorization": f"Basic {credentials}"
            },
            data="grant_type=client_credentials&scope=product.compact",
            timeout=10.0
        )

        if response.status_code == 200:
            token_data = response.json()
            import time
            token_data["expires_at"] = time.time() + token_data.get("expires_in", 1800) - 300
            st.session_state.kroger_token = token_data
            return token_data.get("access_token")
    except Exception as e:
        pass
    return None


def get_kroger_location(token: str, zipcode: str = "90210") -> Optional[str]:
    """Get a Kroger store location ID near the given zipcode."""
    try:
        # Check cache
        cache_key = f"kroger_location_{zipcode}"
        if cache_key in st.session_state:
            return st.session_state[cache_key]

        response = httpx.get(
            KROGER_LOCATION_URL,
            headers={"Authorization": f"Bearer {token}"},
            params={"filter.zipCode.near": zipcode, "filter.limit": 1},
            timeout=10.0
        )

        if response.status_code == 200:
            data = response.json()
            locations = data.get("data", [])
            if locations:
                location_id = locations[0].get("locationId")
                st.session_state[cache_key] = location_id
                return location_id
    except Exception:
        pass
    return None


def search_price_tavily(product_name: str, brand: str) -> dict:
    """Use Tavily API to search for real product prices from any store."""
    try:
        api_key = st.secrets.get("TAVILY_API_KEY", "")
        if not api_key:
            return None

        search_query = f"{brand} {product_name} price grocery" if brand else f"{product_name} price grocery"

        response = httpx.post(
            "https://api.tavily.com/search",
            json={
                "api_key": api_key,
                "query": search_query,
                "search_depth": "basic",
                "max_results": 3,
            },
            timeout=10.0
        )

        if response.status_code == 200:
            data = response.json()
            results = data.get("results", [])

            # Try to extract price and store from results
            for result in results:
                content = result.get("content", "") + " " + result.get("title", "")
                url = result.get("url", "").lower()

                # Extract price pattern ($X.XX)
                price_match = re.search(r'\$(\d+\.?\d*)', content)
                if price_match:
                    price = float(price_match.group(1))

                    # Determine store from URL or content
                    store = "Web"
                    if "walmart" in url or "walmart" in content.lower():
                        store = "Walmart"
                    elif "target" in url or "target" in content.lower():
                        store = "Target"
                    elif "safeway" in url or "safeway" in content.lower():
                        store = "Safeway"
                    elif "costco" in url or "costco" in content.lower():
                        store = "Costco"
                    elif "amazon" in url or "amazon" in content.lower():
                        store = "Amazon"
                    elif "instacart" in url:
                        store = "Instacart"
                    elif "kroger" in url:
                        store = "Kroger"

                    return {"price": price, "store": store}
    except Exception:
        pass
    return None


def estimate_price_llm(product_name: str, brand: str, category: str) -> dict:
    """Use LLM to estimate a typical price for a product."""
    prompt = f"""What is the typical US retail price for this grocery product?
Product: {product_name}
Brand: {brand or "Store brand"}
Category: {category or "Grocery"}

Return ONLY a number (the price in dollars), nothing else. Example: 4.99"""

    try:
        content = call_cloud_llm(prompt)
        if content:
            # Extract number from response
            match = re.search(r'(\d+\.?\d*)', content)
            if match:
                return {"price": float(match.group(1)), "store": "Est."}
    except Exception:
        pass
    return None


def search_kroger_products(query: str, limit: int = 6) -> list:
    """Search Kroger API for products with real prices."""
    token = get_kroger_token()
    if not token:
        return []

    try:
        # Get a location for pricing
        location_id = get_kroger_location(token)

        params = {
            "filter.term": query,
            "filter.limit": limit,
        }
        if location_id:
            params["filter.locationId"] = location_id

        response = httpx.get(
            KROGER_PRODUCT_URL,
            headers={"Authorization": f"Bearer {token}"},
            params=params,
            timeout=10.0
        )

        if response.status_code == 200:
            data = response.json()
            products = data.get("data", [])

            results = []
            for p in products[:limit]:
                # Extract price from items array
                price = None
                data_source = "kroger"
                items = p.get("items", [])
                if items:
                    item = items[0]
                    price_info = item.get("price", {})
                    price = price_info.get("regular") or price_info.get("promo")

                # Get brand and description
                brand = p.get("brand", "")
                description = p.get("description", "")
                categories = p.get("categories", [])
                category = categories[0] if categories else ""
                upc = p.get("upc", "")

                # If no price from Kroger, try Tavily web search, then LLM estimate
                if price is None:
                    # Try Tavily first for real prices
                    tavily_result = search_price_tavily(description, brand)
                    if tavily_result:
                        price = tavily_result["price"]
                        data_source = tavily_result["store"]
                    else:
                        # Fall back to LLM estimate
                        llm_result = estimate_price_llm(description, brand, category)
                        if llm_result:
                            price = llm_result["price"]
                            data_source = llm_result["store"]

                results.append({
                    "name": description,
                    "brand": brand,
                    "category": category,
                    "upc": upc,
                    "avg_price": price,
                    "data_source": data_source,
                })

            return results
    except Exception as e:
        pass

    return []


def search_products_direct(query: str, limit: int = 6) -> list:
    """Search for products using LLM directly (for cloud deployment)."""
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

    try:
        content = call_cloud_llm(prompt)
        if not content:
            return []

        # Extract JSON from response
        json_match = re.search(r'\[.*\]', content, re.DOTALL)
        if json_match:
            products_data = json.loads(json_match.group())

            results = []
            for p in products_data[:limit]:
                if isinstance(p, dict) and p.get("name"):
                    typical_price = p.get("typical_price")
                    if typical_price is not None:
                        try:
                            typical_price = float(typical_price)
                        except (ValueError, TypeError):
                            typical_price = None

                    results.append({
                        "name": p.get("name", "Unknown"),
                        "brand": p.get("brand"),
                        "category": p.get("category"),
                        "data_source": "llm",
                        "avg_price": typical_price,
                    })
            return results
    except Exception as e:
        st.error(f"Search failed: {e}")

    return []


def classify_product_direct(product_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Classify a product using LLM directly (for cloud deployment)."""
    product_name = product_data.get("product_name", "Unknown")
    category = product_data.get("category", "")
    brand = product_data.get("brand", "")

    prompt = f"""You are an expert on SNAP/EBT eligibility rules (7 CFR 271.2).

Determine if this product is eligible for purchase with SNAP/EBT benefits:

Product: {product_name}
Brand: {brand or "Unknown"}
Category: {category or "Unknown"}

SNAP ELIGIBILITY RULES:
ELIGIBLE: Food for home consumption, seeds/plants for food, non-alcoholic beverages, snacks with Nutrition Facts
INELIGIBLE: Alcohol (>0.5% ABV), tobacco, vitamins/supplements (Supplement Facts label), hot prepared foods, food for on-premises consumption, live animals, CBD/cannabis

Respond in this exact JSON format:
{{
    "is_ebt_eligible": true or false,
    "confidence_score": 0.0 to 1.0,
    "category": "ELIGIBLE_STAPLE_FOOD" or "ELIGIBLE_BEVERAGE" or "ELIGIBLE_SNACK_FOOD" or "INELIGIBLE_ALCOHOL" or "INELIGIBLE_SUPPLEMENT" or "INELIGIBLE_HOT_FOOD" or "INELIGIBLE_OTHER",
    "reasoning_chain": ["reason 1", "reason 2", "reason 3"],
    "key_factors": ["factor 1", "factor 2"]
}}

Return ONLY valid JSON, no other text."""

    try:
        content = call_cloud_llm(prompt)
        if not content:
            return None

        # Extract JSON from response
        json_match = re.search(r'\{.*\}', content, re.DOTALL)
        if json_match:
            result = json.loads(json_match.group())
            return result
    except Exception as e:
        st.error(f"Classification failed: {e}")

    return None


def search_products(query: str) -> list:
    """Search for products - tries Kroger API first for real prices, falls back to LLM."""
    if len(query) < 2:
        return []

    # Try Kroger API first for real prices
    kroger_results = search_kroger_products(query)
    if kroger_results:
        return kroger_results

    # Fall back to LLM-generated products if Kroger fails
    if IS_CLOUD or st.session_state.get("llm_mode") == "cloud":
        return search_products_direct(query)

    # Otherwise use local API
    try:
        response = httpx.get(
            f"{API_URL}/search/products",
            params={"q": query, "limit": 6},
            headers=get_llm_headers(),
            timeout=10.0,
        )
        if response.status_code == 200:
            return response.json().get("results", [])
    except Exception:
        pass
    return []


def classify_product(product_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Classify a product - uses direct LLM on cloud, API locally."""
    # Use direct LLM if on cloud or cloud mode is selected
    if IS_CLOUD or st.session_state.get("llm_mode") == "cloud":
        return classify_product_direct(product_data)

    # Otherwise use API
    try:
        response = httpx.post(
            f"{API_URL}/classify",
            json=product_data,
            headers=get_llm_headers(),
            timeout=60.0,
        )
        if response.status_code == 200:
            return response.json()
    except Exception:
        pass
    return None


def add_to_saved_list(product: Dict[str, Any]) -> None:
    """Add a product to the saved list."""
    if "saved_list" not in st.session_state:
        st.session_state.saved_list = []

    # Check if already in list (by name)
    existing_names = [p.get("name") for p in st.session_state.saved_list]
    if product.get("name") not in existing_names:
        st.session_state.saved_list.append(dict(product))


def add_to_history(product: Dict[str, Any], result: Dict[str, Any]) -> None:
    """Add a classification to session history."""
    if "classification_history" not in st.session_state:
        st.session_state.classification_history = []

    from datetime import datetime
    st.session_state.classification_history.append({
        "timestamp": datetime.now().isoformat(),
        "product_name": product.get("name") or product.get("product_name", "Unknown"),
        "is_eligible": result.get("is_ebt_eligible", False),
        "category": result.get("category", ""),
        "confidence": result.get("confidence_score", 0),
        "price": product.get("avg_price"),
        "price_source": product.get("data_source", ""),
    })


def remove_from_saved_list(index: int) -> None:
    """Remove a product from the saved list by index."""
    if "saved_list" in st.session_state and 0 <= index < len(st.session_state.saved_list):
        st.session_state.saved_list.pop(index)


def render_docs_panel() -> None:
    """Render the documentation panel."""
    st.markdown("#### SNAP Eligibility Rules")
    st.markdown("*Based on 7 CFR 271.2*")

    st.markdown("**Eligible Items**")
    st.markdown("""
- Food for home consumption
- Seeds and plants for food
- Non-alcoholic beverages
- Snacks with Nutrition Facts label
- Baby food and formula
- Meat, dairy, produce, bakery
""")

    st.markdown("**Ineligible Items**")
    st.markdown("""
- Alcohol (>0.5% ABV)
- Tobacco products
- Vitamins/supplements
- Hot prepared foods
- Restaurant meals
- Live animals
- CBD/cannabis products
""")

    st.markdown("---")
    st.markdown("**How to Use**")
    st.caption("""
1. Search for a product or enter manually
2. Click "Check" to verify eligibility
3. Use "Add" to save items to your list
4. Click "Check All" to verify multiple items
""")


def render_classify_page() -> None:
    """Render the classification page."""
    inject_styles()

    # Initialize session state
    if "selected_product" not in st.session_state:
        st.session_state.selected_product = None
    if "last_classification" not in st.session_state:
        st.session_state.last_classification = None
    if "saved_list" not in st.session_state:
        st.session_state.saved_list = []
    if "list_results" not in st.session_state:
        st.session_state.list_results = None
    if "show_docs" not in st.session_state:
        st.session_state.show_docs = True

    # Show list results if available (full width)
    if st.session_state.list_results:
        render_list_results()
        return

    # Show single product result if available (full width)
    if st.session_state.selected_product and st.session_state.last_classification:
        render_result_view()
        return

    # Main layout with optional docs panel
    if st.session_state.show_docs:
        col_main, col_docs = st.columns([3, 1])
    else:
        col_main = st.container()
        col_docs = None

    with col_main:
        render_search_view()

    if col_docs:
        with col_docs:
            # Docs toggle at top
            if st.button("Hide Guide", key="hide_docs", use_container_width=True):
                st.session_state.show_docs = False
                st.rerun()
            st.markdown("")
            render_docs_panel()
    else:
        # Show button to restore docs in the search view
        pass


def render_search_view() -> None:
    """Render the search interface with saved list."""

    # Header with docs toggle
    col_header, col_toggle = st.columns([4, 1])
    with col_header:
        st.markdown("### Search Products")
    with col_toggle:
        if not st.session_state.get("show_docs", True):
            if st.button("Show Guide", key="show_docs_btn"):
                st.session_state.show_docs = True
                st.rerun()

    # Search and saved list side by side
    col_search, col_list = st.columns([3, 2])

    with col_search:
        # Search box
        query = st.text_input(
            "Search products",
            placeholder="Search by product name (e.g., milk, chips, energy drink)...",
            label_visibility="collapsed",
            key="search_query",
        )

        # Search results
        if query and len(query) >= 2:
            with st.spinner("Searching..."):
                results = search_products(query)

            if results:
                for idx, product in enumerate(results):
                    render_product_card(product, idx)
            else:
                st.info("No products found. Try a different search term.")

        # Manual entry (compact)
        with st.expander("Enter product manually"):
            render_manual_entry()

    with col_list:
        render_saved_list()


def render_product_card(product: Dict[str, Any], index: int = 0) -> None:
    """Render a product card with Check and Add buttons."""
    name = product.get("name", "Unknown Product")
    brand = product.get("brand", "")
    category = product.get("category", "")

    # Format price with source indicator
    price_text = ""
    data_source = product.get("data_source", "")
    if product.get("avg_price"):
        price_text = f"${product['avg_price']:.2f}"

    # Check if already in saved list
    saved_names = [p.get("name") for p in st.session_state.get("saved_list", [])]
    is_saved = name in saved_names

    # Card layout
    col1, col2, col3, col4 = st.columns([2.5, 1, 0.8, 0.8])

    with col1:
        display_name = f"**{name}**"
        if brand:
            display_name += f" - {brand}"
        st.markdown(display_name)
        if category:
            st.caption(category)

    with col2:
        if price_text:
            if data_source == "Est.":
                st.markdown(f"~{price_text}")
                st.caption("Est.")
            elif data_source:
                st.markdown(f"{price_text}")
                st.caption(data_source)
            else:
                st.markdown(price_text)

    with col3:
        if st.button("Check", key=f"check_{index}", type="primary"):
            product_data = {
                "product_id": product.get("upc") or f"SEARCH-{hash(name)}",
                "product_name": name,
                "description": product.get("description"),
                "category": category,
                "brand": brand,
            }

            with st.spinner("Checking..."):
                result = classify_product(product_data)

            if result:
                st.session_state.selected_product = dict(product)
                st.session_state.last_classification = result
                add_to_history(product, result)
                st.rerun()

    with col4:
        if is_saved:
            st.button("Added", key=f"added_{index}", disabled=True)
        else:
            if st.button("Add", key=f"add_{index}"):
                add_to_saved_list(product)
                st.rerun()


def render_saved_list() -> None:
    """Render the saved list panel."""
    saved_list = st.session_state.get("saved_list", [])
    count = len(saved_list)

    st.markdown(f"### Saved List <span class='list-count'>{count}</span>", unsafe_allow_html=True)

    if not saved_list:
        st.caption("Add products from search results to check multiple items at once.")
        return

    # List items
    for idx, product in enumerate(saved_list):
        col1, col2 = st.columns([4, 1])

        with col1:
            name = product.get("name", "Unknown")
            price = product.get("avg_price")
            if price:
                st.markdown(f"**{name}** - ${price:.2f}")
            else:
                st.markdown(f"**{name}**")

        with col2:
            if st.button("X", key=f"remove_{idx}"):
                remove_from_saved_list(idx)
                st.rerun()

    st.markdown("")

    # Action buttons
    col_check, col_clear = st.columns(2)

    with col_check:
        if st.button("Check All", type="primary", use_container_width=True):
            check_all_saved_products()

    with col_clear:
        if st.button("Clear All", use_container_width=True):
            st.session_state.saved_list = []
            st.rerun()


def check_all_saved_products() -> None:
    """Check eligibility for all saved products."""
    saved_list = st.session_state.get("saved_list", [])
    if not saved_list:
        return

    results = []
    progress = st.progress(0, text="Checking eligibility...")

    for idx, product in enumerate(saved_list):
        name = product.get("name", "Unknown")
        progress.progress((idx + 1) / len(saved_list), text=f"Checking {name}...")

        product_data = {
            "product_id": product.get("upc") or f"LIST-{hash(name)}",
            "product_name": name,
            "description": product.get("description"),
            "category": product.get("category"),
            "brand": product.get("brand"),
        }

        result = classify_product(product_data)
        results.append({
            "product": product,
            "result": result,
        })

    progress.empty()
    st.session_state.list_results = results
    st.rerun()


def render_list_results() -> None:
    """Render results for all checked products."""
    results = st.session_state.list_results

    # Back button
    if st.button("Back to search"):
        st.session_state.list_results = None
        st.rerun()

    st.markdown("")
    st.markdown("### Eligibility Results")

    # Summary stats
    eligible_count = sum(1 for r in results if r.get("result", {}).get("is_ebt_eligible", False))
    total_count = len(results)
    total_price = sum(r.get("product", {}).get("avg_price", 0) or 0 for r in results)
    ebt_covered = sum(
        r.get("product", {}).get("avg_price", 0) or 0
        for r in results
        if r.get("result", {}).get("is_ebt_eligible", False)
    )

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Total Items", total_count)
    with col2:
        st.metric("EBT Eligible", eligible_count)
    with col3:
        st.metric("Total Price", f"${total_price:.2f}")
    with col4:
        st.metric("EBT Covers", f"${ebt_covered:.2f}")

    st.markdown("")

    # Results list
    for item in results:
        product = item.get("product", {})
        result = item.get("result", {})

        name = product.get("name", "Unknown")
        price = product.get("avg_price", 0) or 0
        is_eligible = result.get("is_ebt_eligible", False) if result else False
        confidence = result.get("confidence_score", 0) if result else 0

        # Row styling based on eligibility
        if is_eligible:
            bg_color = "rgba(16, 163, 127, 0.1)"
            badge = f"<span style='background: {COLORS['success']}; color: white; padding: 4px 12px; border-radius: 12px; font-size: 12px;'>ELIGIBLE</span>"
        else:
            bg_color = "rgba(239, 68, 68, 0.1)"
            badge = f"<span style='background: {COLORS['error']}; color: white; padding: 4px 12px; border-radius: 12px; font-size: 12px;'>NOT ELIGIBLE</span>"

        st.markdown(f"""
        <div style="background: {bg_color}; padding: 16px; border-radius: 8px; margin: 8px 0;">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <div>
                    <strong>{name}</strong>
                    <span style="color: {COLORS['muted']}; margin-left: 12px;">${price:.2f}</span>
                </div>
                <div>
                    {badge}
                    <span style="color: {COLORS['muted']}; margin-left: 8px; font-size: 12px;">{confidence * 100:.0f}%</span>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("")

    # Summary box
    you_pay = total_price - ebt_covered
    st.markdown(f"""
    <div style="background: white; padding: 20px; border-radius: 12px; border: 2px solid {COLORS['accent']}; margin-top: 16px;">
        <div style="display: flex; justify-content: space-between;">
            <div>
                <div style="color: {COLORS['muted']}; font-size: 12px; text-transform: uppercase;">Total</div>
                <div style="font-size: 24px; font-weight: 600;">${total_price:.2f}</div>
            </div>
            <div>
                <div style="color: {COLORS['muted']}; font-size: 12px; text-transform: uppercase;">EBT Covers</div>
                <div style="font-size: 24px; font-weight: 600; color: {COLORS['success']};">${ebt_covered:.2f}</div>
            </div>
            <div>
                <div style="color: {COLORS['muted']}; font-size: 12px; text-transform: uppercase;">You Pay</div>
                <div style="font-size: 24px; font-weight: 600; color: {COLORS['error'] if you_pay > 0 else COLORS['success']};">${you_pay:.2f}</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)


def render_result_view() -> None:
    """Render single product classification result."""
    product = st.session_state.selected_product
    result = st.session_state.last_classification

    # Back button
    if st.button("Back to search"):
        st.session_state.selected_product = None
        st.session_state.last_classification = None
        st.rerun()

    st.markdown("")

    # Product name
    name = product.get("name", "Unknown Product")
    st.markdown(f"### {name}")

    st.markdown("")

    # Result badge
    is_eligible = result.get("is_ebt_eligible", False)
    confidence = result.get("confidence_score", 0)

    if is_eligible:
        st.markdown(f"""
        <div class="result-badge result-eligible">
            EBT ELIGIBLE
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown(f"""
        <div class="result-badge result-ineligible">
            NOT ELIGIBLE
        </div>
        """, unsafe_allow_html=True)

    st.markdown("")
    st.caption(f"Confidence: {confidence * 100:.0f}%")

    # EBT Coverage section
    if product.get("avg_price"):
        price = product.get("avg_price", 0)
        st.markdown("")
        st.markdown("<p class='section-header'>EBT Coverage</p>", unsafe_allow_html=True)

        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Price", f"${price:.2f}")
        with col2:
            st.metric("EBT Covers", f"${price:.2f}" if is_eligible else "$0.00")
        with col3:
            st.metric("You Pay", "$0.00" if is_eligible else f"${price:.2f}")

    # Reasoning
    reasoning = result.get("reasoning_chain", [])
    if reasoning:
        st.markdown("")
        st.markdown("<p class='section-header'>Why?</p>", unsafe_allow_html=True)
        for i, step in enumerate(reasoning, 1):
            st.markdown(f"{i}. {step}")


def render_manual_entry() -> None:
    """Render simplified manual entry form."""
    col1, col2 = st.columns(2)

    with col1:
        product_name = st.text_input(
            "Product name",
            placeholder="e.g., Monster Energy Drink",
            key="manual_name",
        )

    with col2:
        category = st.selectbox(
            "Category",
            options=["", "Produce", "Dairy", "Meat", "Bakery", "Beverages",
                     "Snacks", "Frozen Foods", "Canned Goods", "Prepared Foods", "Other"],
            key="manual_category",
        )

    col_check, col_add = st.columns(2)

    with col_check:
        if st.button("Check", type="primary", key="manual_check"):
            if not product_name:
                st.error("Enter a product name")
            else:
                product_data = {
                    "product_id": f"MANUAL-{hash(product_name)}",
                    "product_name": product_name,
                    "category": category if category else None,
                }

                st.session_state.selected_product = {
                    "name": product_name,
                    "category": category,
                }

                with st.spinner("Checking..."):
                    result = classify_product(product_data)

                if result:
                    st.session_state.last_classification = result
                    add_to_history(st.session_state.selected_product, result)
                    st.rerun()

    with col_add:
        if st.button("Add to List", key="manual_add"):
            if product_name:
                add_to_saved_list({
                    "name": product_name,
                    "category": category,
                })
                st.rerun()
