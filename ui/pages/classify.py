"""Single classification page."""

import streamlit as st
import httpx
import os

from ui.components.product_form import render_product_form
from ui.components.result_display import render_result_display
from ui.components.reasoning_chain import render_reasoning_chain


# API URL from environment or default
API_URL = os.environ.get("API_URL", "http://localhost:8000")


def render_classify_page() -> None:
    """Render the single classification page."""
    st.title("Single Product Classification")
    st.markdown(
        "Classify a product for EBT/SNAP eligibility based on USDA regulations."
    )

    # Product form
    product_data = render_product_form()

    if product_data:
        with st.spinner("Classifying product..."):
            try:
                # Call API
                response = httpx.post(
                    f"{API_URL}/classify",
                    json=product_data,
                    timeout=60.0,
                )

                if response.status_code == 200:
                    result = response.json()

                    st.markdown("---")
                    st.header("Classification Result")

                    # Display result
                    render_result_display(result)

                    # Display reasoning
                    st.markdown("---")
                    st.header("Explanation")
                    render_reasoning_chain(result)

                    # Store result in session for potential challenge
                    st.session_state["last_classification"] = result

                else:
                    st.error(f"API Error: {response.status_code}")
                    st.json(response.json())

            except httpx.ConnectError:
                st.error(
                    "Could not connect to the API. "
                    "Make sure the API server is running at "
                    f"`{API_URL}`"
                )
            except Exception as e:
                st.error(f"Error: {str(e)}")

    # Quick test products
    st.markdown("---")
    with st.expander("Quick Test Products"):
        st.markdown("Click to auto-fill the form with test data:")

        col1, col2 = st.columns(2)

        with col1:
            st.markdown("**Eligible Products:**")
            if st.button("Fresh Apples (Produce)"):
                st.session_state["test_product"] = {
                    "product_id": "TEST-001",
                    "product_name": "Fresh Apples",
                    "category": "Produce",
                    "nutrition_label_type": "nutrition_facts",
                }
                st.rerun()

            if st.button("Monster Energy (Beverage)"):
                st.session_state["test_product"] = {
                    "product_id": "TEST-002",
                    "product_name": "Monster Energy Drink",
                    "category": "Beverages",
                    "nutrition_label_type": "nutrition_facts",
                }
                st.rerun()

        with col2:
            st.markdown("**Ineligible Products:**")
            if st.button("Budweiser Beer (Alcohol)"):
                st.session_state["test_product"] = {
                    "product_id": "TEST-003",
                    "product_name": "Budweiser Beer",
                    "category": "Beverages",
                    "alcohol_content": 0.05,
                }
                st.rerun()

            if st.button("Centrum Vitamin (Supplement)"):
                st.session_state["test_product"] = {
                    "product_id": "TEST-004",
                    "product_name": "Centrum Multivitamin",
                    "category": "Health",
                    "nutrition_label_type": "supplement_facts",
                }
                st.rerun()
