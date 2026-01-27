"""EBT Eligibility Check - Clean, minimal design."""

import streamlit as st
import httpx
import os
from typing import Optional, Dict, Any

# API URL from environment or default
API_URL = os.environ.get("API_URL", "http://localhost:8000")

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

        /* Product card */
        .product-card {{
            background: white;
            border-radius: 12px;
            padding: 20px;
            margin: 8px 0;
            box-shadow: 0 1px 3px rgba(0,0,0,0.08);
            border: 1px solid #F0F0F0;
            cursor: pointer;
            transition: all 0.2s ease;
        }}
        .product-card:hover {{
            box-shadow: 0 4px 12px rgba(0,0,0,0.1);
            border-color: {COLORS['accent']};
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

        /* Coverage card */
        .coverage-card {{
            background: white;
            border-radius: 12px;
            padding: 24px;
            margin: 16px 0;
            box-shadow: 0 1px 3px rgba(0,0,0,0.08);
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
        .stButton > button[kind="primary"] {{
            background: {COLORS['accent']};
            border: none;
        }}

        /* Metrics cleanup */
        [data-testid="stMetricValue"] {{
            font-size: 24px;
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
    </style>
    """, unsafe_allow_html=True)


def get_llm_headers() -> dict:
    """Get headers for LLM mode from session state."""
    headers = {}
    if st.session_state.get("llm_mode") == "cloud" and st.session_state.get("ollama_cloud_key"):
        headers["X-Ollama-Mode"] = "cloud"
        headers["X-Ollama-Cloud-Key"] = st.session_state.ollama_cloud_key
    return headers


def search_products(query: str) -> list:
    """Search for products via API."""
    if len(query) < 2:
        return []
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
    """Classify a product via API."""
    try:
        response = httpx.post(
            f"{API_URL}/classify",
            json=product_data,
            headers=get_llm_headers(),
            timeout=60.0,
        )
        if response.status_code == 200:
            return response.json()
        st.error(f"Classification failed: {response.status_code}")
    except httpx.ConnectError:
        st.error(f"Could not connect to API at {API_URL}")
    except Exception as e:
        st.error(f"Error: {str(e)}")
    return None


def render_classify_page() -> None:
    """Render the classification page."""
    inject_styles()

    # Initialize session state
    if "selected_product" not in st.session_state:
        st.session_state.selected_product = None
    if "last_classification" not in st.session_state:
        st.session_state.last_classification = None

    # Header
    st.markdown("## EBT Eligibility Check")
    st.caption("Check if a product qualifies for SNAP/EBT benefits")

    # Show results view if product selected and classified
    if st.session_state.selected_product and st.session_state.last_classification:
        render_result_view()
        return

    # Show product detail if selected but not yet classified
    if st.session_state.selected_product:
        render_product_detail()
        return

    # Default: show search
    render_search_view()


def render_search_view() -> None:
    """Render the search interface."""
    st.markdown("")

    # Search box
    query = st.text_input(
        "Search products",
        placeholder="Search by product name or UPC...",
        label_visibility="collapsed",
        key="search_query",
    )

    # Search results
    if query and len(query) >= 2:
        results = search_products(query)

        if results:
            st.markdown("")
            for idx, product in enumerate(results):
                render_product_card(product, idx)
        else:
            st.markdown("")
            st.info("No products found. Try a different search term.")

    # Manual entry option
    st.markdown("---")
    st.markdown("<p class='section-header'>Or enter manually</p>", unsafe_allow_html=True)
    render_manual_entry()


def render_product_card(product: Dict[str, Any], index: int = 0) -> None:
    """Render a clickable product card."""
    name = product.get("name", "Unknown Product")
    brand = product.get("brand", "")
    category = product.get("category", "")

    # Format price
    price_text = ""
    if product.get("avg_price"):
        min_p = product.get("min_price", product["avg_price"])
        max_p = product.get("max_price", product["avg_price"])
        if min_p != max_p:
            price_text = f"${min_p:.2f} - ${max_p:.2f}"
        else:
            price_text = f"${product['avg_price']:.2f}"

    # Card layout
    col1, col2, col3 = st.columns([3, 1, 1])

    with col1:
        display_name = f"**{name}**"
        if brand:
            display_name = f"**{name}** by {brand}"
        st.markdown(display_name)
        if category:
            st.caption(category)

    with col2:
        if price_text:
            st.markdown(f"**{price_text}**")

    with col3:
        # Use index-based unique key for reliable button identification
        if st.button("Check", key=f"check_product_{index}", type="primary"):
            # Directly classify the product
            product_data = {
                "product_id": product.get("upc") or product.get("fdc_id") or f"SEARCH-{hash(name)}",
                "product_name": name,
                "description": product.get("description") or product.get("ingredients"),
                "category": category,
                "brand": brand,
                "upc": product.get("upc"),
            }

            with st.spinner("Checking eligibility..."):
                result = classify_product(product_data)

            if result:
                st.session_state.selected_product = dict(product)
                st.session_state.last_classification = result
                st.rerun()


def render_product_detail() -> None:
    """Render selected product details with classify option."""
    product = st.session_state.selected_product

    # Back button
    if st.button("Back to search"):
        st.session_state.selected_product = None
        st.rerun()

    st.markdown("")

    # Product info
    name = product.get("name", "Unknown Product")
    brand = product.get("brand", "")
    category = product.get("category", "")

    st.markdown(f"### {name}")
    if brand:
        st.caption(f"Brand: {brand}")
    if category:
        st.caption(f"Category: {category}")

    # Price display
    if product.get("avg_price"):
        min_p = product.get("min_price", product["avg_price"])
        max_p = product.get("max_price", product["avg_price"])
        if min_p != max_p:
            st.markdown(f"**${min_p:.2f} - ${max_p:.2f}**")
        else:
            st.markdown(f"**${product['avg_price']:.2f}**")

    st.markdown("")

    # Classify button
    if st.button("Check EBT Eligibility", type="primary", use_container_width=True):
        product_data = {
            "product_id": product.get("upc") or product.get("fdc_id") or f"SEARCH-{hash(name)}",
            "product_name": name,
            "description": product.get("description") or product.get("ingredients"),
            "category": category,
            "brand": brand,
            "upc": product.get("upc"),
        }

        with st.spinner("Checking eligibility..."):
            result = classify_product(product_data)

        if result:
            st.session_state.last_classification = result
            st.rerun()


def render_result_view() -> None:
    """Render the classification result."""
    product = st.session_state.selected_product
    result = st.session_state.last_classification

    # New search button
    if st.button("New search"):
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

    # Confidence
    st.caption(f"Confidence: {confidence * 100:.0f}%")

    # Category/reason
    category = result.get("classification_category", "")
    if category:
        st.caption(f"Category: {category.replace('_', ' ').title()}")

    st.markdown("")

    # EBT Coverage section
    if product.get("avg_price"):
        render_coverage_section(product, is_eligible)

    # Reasoning section
    render_reasoning_section(result)


def render_coverage_section(product: Dict[str, Any], is_eligible: bool) -> None:
    """Render EBT coverage breakdown."""
    price = product.get("avg_price", 0)

    st.markdown("<p class='section-header'>EBT Coverage</p>", unsafe_allow_html=True)

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("Price", f"${price:.2f}")

    with col2:
        if is_eligible:
            st.metric("EBT Covers", f"${price:.2f}")
        else:
            st.metric("EBT Covers", "$0.00")

    with col3:
        if is_eligible:
            st.metric("You Pay", "$0.00")
        else:
            st.metric("You Pay", f"${price:.2f}")

    if is_eligible:
        st.markdown(f"""
        <div style="background: rgba(16, 163, 127, 0.1); padding: 12px 16px; border-radius: 8px; color: {COLORS['success']}; margin-top: 8px;">
            Fully covered by SNAP/EBT benefits
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown(f"""
        <div style="background: rgba(239, 68, 68, 0.1); padding: 12px 16px; border-radius: 8px; color: {COLORS['error']}; margin-top: 8px;">
            Not covered - full price required
        </div>
        """, unsafe_allow_html=True)

    st.markdown("")


def render_reasoning_section(result: Dict[str, Any]) -> None:
    """Render reasoning in a clean format."""
    reasoning = result.get("reasoning_chain", [])
    key_factors = result.get("key_factors", [])

    if reasoning:
        st.markdown("<p class='section-header'>Why this classification?</p>", unsafe_allow_html=True)
        for i, step in enumerate(reasoning, 1):
            st.markdown(f"{i}. {step}")

    if key_factors:
        st.markdown("")
        st.markdown("<p class='section-header'>Key factors</p>", unsafe_allow_html=True)
        for factor in key_factors:
            st.markdown(f"- {factor}")

    # Data sources (collapsed)
    data_sources = result.get("data_sources_used", [])
    if data_sources:
        with st.expander("Data sources"):
            for source in data_sources:
                st.caption(f"- {source}")


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

    if st.button("Check EBT Eligibility", type="primary", key="manual_check"):
        if not product_name:
            st.error("Please enter a product name")
        else:
            product_data = {
                "product_id": f"MANUAL-{hash(product_name)}",
                "product_name": product_name,
                "category": category if category else None,
            }

            # Store as selected product for result display
            st.session_state.selected_product = {
                "name": product_name,
                "category": category,
            }

            with st.spinner("Checking eligibility..."):
                result = classify_product(product_data)

            if result:
                st.session_state.last_classification = result
                st.rerun()
