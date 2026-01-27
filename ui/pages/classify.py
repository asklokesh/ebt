"""EBT Eligibility Check - Clean, minimal design with saved list feature."""

import streamlit as st
import httpx
import os
from typing import Optional, Dict, Any, List

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


def remove_from_saved_list(index: int) -> None:
    """Remove a product from the saved list by index."""
    if "saved_list" in st.session_state and 0 <= index < len(st.session_state.saved_list):
        st.session_state.saved_list.pop(index)


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

    # Header
    st.markdown("## EBT Eligibility Check")
    st.caption("Check if a product qualifies for SNAP/EBT benefits")

    # Show list results if available
    if st.session_state.list_results:
        render_list_results()
        return

    # Show single product result if available
    if st.session_state.selected_product and st.session_state.last_classification:
        render_result_view()
        return

    # Default: show search with saved list
    render_search_view()


def render_search_view() -> None:
    """Render the search interface with saved list."""

    # Two columns: search and saved list
    col_search, col_list = st.columns([3, 2])

    with col_search:
        st.markdown("### Search Products")

        # Search box
        query = st.text_input(
            "Search products",
            placeholder="Search by product name...",
            label_visibility="collapsed",
            key="search_query",
        )

        # Search results
        if query and len(query) >= 2:
            results = search_products(query)

            if results:
                for idx, product in enumerate(results):
                    render_product_card(product, idx)
            else:
                st.info("No products found. Try a different search term.")

        # Manual entry
        st.markdown("---")
        st.markdown("<p class='section-header'>Or enter manually</p>", unsafe_allow_html=True)
        render_manual_entry()

    with col_list:
        render_saved_list()


def render_product_card(product: Dict[str, Any], index: int = 0) -> None:
    """Render a product card with Check and Add buttons."""
    name = product.get("name", "Unknown Product")
    brand = product.get("brand", "")
    category = product.get("category", "")

    # Format price
    price_text = ""
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
                    st.rerun()

    with col_add:
        if st.button("Add to List", key="manual_add"):
            if product_name:
                add_to_saved_list({
                    "name": product_name,
                    "category": category,
                })
                st.rerun()
