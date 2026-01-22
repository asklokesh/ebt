"""Single classification page with search-first UX."""

import streamlit as st
import httpx
import os
from typing import Optional, Dict, Any

from ui.components.result_display import render_result_display
from ui.components.reasoning_chain import render_reasoning_chain

# API URL from environment or default
API_URL = os.environ.get("API_URL", "http://localhost:8000")


def search_products(query: str) -> list:
    """Search for products via API."""
    if len(query) < 2:
        return []

    try:
        response = httpx.get(
            f"{API_URL}/search/products",
            params={"q": query, "limit": 8},
            timeout=10.0,
        )
        if response.status_code == 200:
            data = response.json()
            return data.get("results", [])
    except Exception:
        pass
    return []


def classify_product(product_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Classify a product via API."""
    try:
        response = httpx.post(
            f"{API_URL}/classify",
            json=product_data,
            timeout=60.0,
        )
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"Classification failed: {response.status_code}")
            return None
    except httpx.ConnectError:
        st.error(f"Could not connect to API at {API_URL}")
        return None
    except Exception as e:
        st.error(f"Error: {str(e)}")
        return None


def render_classify_page() -> None:
    """Render the single classification page."""
    st.title("EBT Eligibility Check")
    st.caption("Check if a product is eligible for SNAP/EBT benefits")

    # Initialize session state
    if "selected_product" not in st.session_state:
        st.session_state.selected_product = None
    if "last_classification" not in st.session_state:
        st.session_state.last_classification = None

    # If product is selected, show the product card
    if st.session_state.selected_product:
        render_product_card(st.session_state.selected_product)
        return

    # Main search input
    st.markdown("### Search for a product")

    search_input = st.text_input(
        "Product name or UPC",
        placeholder="Type product name (e.g., 'milk', 'energy drink', 'vitamins')",
        label_visibility="collapsed",
        key="product_search_input",
    )

    # Show search suggestions
    if search_input and len(search_input) >= 2:
        suggestions = search_products(search_input)

        if suggestions:
            st.markdown("**Select a product:**")

            for i, product in enumerate(suggestions):
                product_label = product.get("name", "Unknown")
                if product.get("brand"):
                    product_label = f"{product['brand']} - {product_label}"
                if product.get("category"):
                    product_label += f" ({product['category']})"

                if st.button(
                    product_label,
                    key=f"select_product_{i}",
                    use_container_width=True,
                ):
                    st.session_state.selected_product = product
                    st.session_state.last_classification = None
                    st.rerun()
        else:
            st.info("No products found. Try a different search or use manual entry below.")

    st.markdown("---")

    # Show manual entry form
    render_manual_entry_form()


def render_product_card(product: Dict[str, Any]) -> None:
    """Render the selected product card with classify button."""
    st.markdown("### Selected Product")

    # Product info card
    col1, col2 = st.columns([3, 1])

    with col1:
        st.markdown(f"**{product.get('name', 'Unknown Product')}**")

        if product.get("brand"):
            st.caption(f"Brand: {product['brand']}")
        if product.get("category"):
            st.caption(f"Category: {product['category']}")
        if product.get("upc"):
            st.caption(f"UPC: {product['upc']}")

    with col2:
        if st.button("Change", key="change_product_btn", use_container_width=True):
            st.session_state.selected_product = None
            st.session_state.last_classification = None
            st.rerun()

    # Advanced options (collapsed by default)
    with st.expander("Additional Details (optional)"):
        col_a, col_b = st.columns(2)

        with col_a:
            is_hot = st.checkbox("Sold hot (ready to eat)", key="opt_hot")
            is_onsite = st.checkbox("For on-site consumption", key="opt_onsite")
            has_alcohol = st.checkbox("Contains alcohol", key="opt_alcohol")

        with col_b:
            has_tobacco = st.checkbox("Contains tobacco/nicotine", key="opt_tobacco")
            is_supplement = st.checkbox("Supplement Facts label", key="opt_supplement")
            has_cbd = st.checkbox("Contains CBD/cannabis", key="opt_cbd")

        if has_alcohol:
            alcohol_pct = st.slider("Alcohol % (ABV)", 0.0, 100.0, 5.0, 0.1, key="opt_alcohol_pct")
        else:
            alcohol_pct = 0.0

    # Classify button
    st.markdown("")
    if st.button("Check EBT Eligibility", type="primary", use_container_width=True, key="classify_btn"):
        # Build product data
        product_data = {
            "product_id": product.get("upc") or product.get("fdc_id") or f"SEARCH-{hash(product.get('name', ''))}",
            "product_name": product.get("name", "Unknown"),
            "description": product.get("description") or product.get("ingredients"),
            "category": product.get("category"),
            "brand": product.get("brand"),
            "upc": product.get("upc"),
            "is_hot_at_sale": is_hot,
            "is_for_onsite_consumption": is_onsite,
            "alcohol_content": alcohol_pct / 100 if alcohol_pct > 0 else None,
            "contains_tobacco": has_tobacco,
            "contains_cbd_cannabis": has_cbd,
            "nutrition_label_type": "supplement_facts" if is_supplement else None,
        }

        with st.spinner("Checking eligibility..."):
            result = classify_product(product_data)

        if result:
            st.session_state.last_classification = result

    # Show results if available
    if st.session_state.last_classification:
        result = st.session_state.last_classification
        st.markdown("---")
        st.header("Result")
        render_result_display(result)

        st.markdown("---")
        st.header("Explanation")
        render_reasoning_chain(result)


def render_manual_entry_form() -> None:
    """Render manual product entry form."""
    st.markdown("### Or enter product details manually")

    with st.form("manual_product_form"):
        col1, col2 = st.columns(2)

        with col1:
            product_name = st.text_input(
                "Product Name *",
                placeholder="e.g., Monster Energy Drink",
            )
            category = st.selectbox(
                "Category",
                options=[
                    "",
                    "Produce",
                    "Dairy",
                    "Meat",
                    "Bakery",
                    "Beverages",
                    "Snacks",
                    "Frozen Foods",
                    "Canned Goods",
                    "Baby Food",
                    "Supplements",
                    "Alcohol",
                    "Tobacco",
                    "Prepared Foods",
                    "Other",
                ],
            )

        with col2:
            brand = st.text_input("Brand", placeholder="e.g., Monster")
            upc = st.text_input("UPC Code", placeholder="12-digit barcode")

        # Product attributes
        st.markdown("**Product Attributes**")
        attr_col1, attr_col2 = st.columns(2)

        with attr_col1:
            is_hot = st.checkbox("Sold hot (ready to eat)", key="manual_hot")
            is_onsite = st.checkbox("For on-site consumption", key="manual_onsite")
            has_tobacco = st.checkbox("Contains tobacco/nicotine", key="manual_tobacco")

        with attr_col2:
            has_cbd = st.checkbox("Contains CBD/cannabis", key="manual_cbd")
            is_supplement = st.checkbox("Has Supplement Facts label", key="manual_supplement")
            alcohol_content = st.number_input(
                "Alcohol % (0 if none)",
                min_value=0.0,
                max_value=100.0,
                value=0.0,
                step=0.1,
                key="manual_alcohol",
            )

        submitted = st.form_submit_button(
            "Check EBT Eligibility",
            type="primary",
            use_container_width=True,
        )

        if submitted:
            if not product_name:
                st.error("Product name is required")
            else:
                product_data = {
                    "product_id": upc or f"MANUAL-{hash(product_name)}",
                    "product_name": product_name,
                    "category": category if category else None,
                    "brand": brand if brand else None,
                    "upc": upc if upc else None,
                    "is_hot_at_sale": is_hot,
                    "is_for_onsite_consumption": is_onsite,
                    "alcohol_content": alcohol_content / 100 if alcohol_content > 0 else None,
                    "contains_tobacco": has_tobacco,
                    "contains_cbd_cannabis": has_cbd,
                    "nutrition_label_type": "supplement_facts" if is_supplement else None,
                }

                with st.spinner("Checking eligibility..."):
                    result = classify_product(product_data)

                if result:
                    st.session_state.last_classification = result

    # Show results if available (outside form)
    if st.session_state.get("last_classification") and not st.session_state.get("selected_product"):
        result = st.session_state.last_classification
        st.markdown("---")
        st.header("Result")
        render_result_display(result)

        st.markdown("---")
        st.header("Explanation")
        render_reasoning_chain(result)
