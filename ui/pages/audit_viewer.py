"""Audit trail viewer page."""

import streamlit as st
import httpx
import os
import pandas as pd
from datetime import datetime, timedelta

# API URL from environment or default
API_URL = os.environ.get("API_URL", "http://localhost:8000")

# Check if we're running on Streamlit Cloud (no local API)
IS_CLOUD = os.environ.get("STREAMLIT_SHARING_MODE") or not os.environ.get("API_URL")


def render_audit_page() -> None:
    """Render the audit trail viewer page."""
    st.title("Classification History")

    # On cloud, use session-based history
    if IS_CLOUD:
        render_session_history()
        return

    st.markdown("View and search classification history.")

    # Filters
    st.subheader("Filters")

    col1, col2, col3 = st.columns(3)

    with col1:
        # Date range
        date_options = {
            "All Time": None,
            "Last 24 Hours": timedelta(days=1),
            "Last 7 Days": timedelta(days=7),
            "Last 30 Days": timedelta(days=30),
        }
        date_filter = st.selectbox("Date Range", options=list(date_options.keys()))

    with col2:
        # Eligibility filter
        eligibility_options = {
            "All": None,
            "Eligible Only": True,
            "Ineligible Only": False,
        }
        eligibility_filter = st.selectbox(
            "Eligibility", options=list(eligibility_options.keys())
        )

    with col3:
        # Challenge filter
        challenge_options = {
            "All": None,
            "Challenged": True,
            "Not Challenged": False,
        }
        challenge_filter = st.selectbox(
            "Challenge Status", options=list(challenge_options.keys())
        )

    # Additional filters
    col4, col5 = st.columns(2)

    with col4:
        product_id_filter = st.text_input(
            "Product ID",
            placeholder="Filter by product ID",
        )

    with col5:
        limit = st.number_input(
            "Results per page",
            min_value=10,
            max_value=1000,
            value=100,
            step=10,
        )

    # Build query params
    params = {"limit": limit}

    if date_options[date_filter]:
        start_date = datetime.utcnow() - date_options[date_filter]
        params["start_date"] = start_date.isoformat()

    if eligibility_options[eligibility_filter] is not None:
        params["is_ebt_eligible"] = eligibility_options[eligibility_filter]

    if challenge_options[challenge_filter] is not None:
        params["was_challenged"] = challenge_options[challenge_filter]

    if product_id_filter:
        params["product_id"] = product_id_filter

    # Fetch data
    if st.button("Search", type="primary") or "audit_results" not in st.session_state:
        with st.spinner("Loading audit records..."):
            try:
                response = httpx.get(
                    f"{API_URL}/audit-trail",
                    params=params,
                    timeout=30.0,
                )

                if response.status_code == 200:
                    st.session_state["audit_results"] = response.json()
                else:
                    st.error(f"API Error: {response.status_code}")
                    st.session_state["audit_results"] = None

            except httpx.ConnectError:
                st.error("Could not connect to the API.")
                st.session_state["audit_results"] = None
            except Exception as e:
                st.error(f"Error: {str(e)}")
                st.session_state["audit_results"] = None

    # Display results
    if st.session_state.get("audit_results"):
        results = st.session_state["audit_results"]

        st.markdown("---")
        st.subheader(f"Results ({results.get('returned_records', 0)} of {results.get('total_records', 0)})")

        records = results.get("records", [])

        if records:
            # Convert to DataFrame
            df_data = []
            for record in records:
                df_data.append({
                    "Timestamp": record.get("timestamp", "")[:19],
                    "Product ID": record.get("product_id"),
                    "Product Name": record.get("product_name"),
                    "Eligible": "Yes" if record.get("is_ebt_eligible") else "No",
                    "Category": record.get("classification_category", "").replace("_", " "),
                    "Confidence": f"{record.get('confidence_score', 0) * 100:.0f}%",
                    "Challenged": "Yes" if record.get("was_challenged") else "No",
                    "Audit ID": record.get("audit_id"),
                })

            df = pd.DataFrame(df_data)

            # Display table
            st.dataframe(
                df,
                width="stretch",
                column_config={
                    "Audit ID": st.column_config.TextColumn(width="small"),
                },
            )

            # Record details
            st.markdown("---")
            st.subheader("Record Details")

            audit_id = st.selectbox(
                "Select Audit ID to view details",
                options=[r.get("audit_id") for r in records],
                format_func=lambda x: f"{x[:8]}... - {next((r.get('product_name') for r in records if r.get('audit_id') == x), 'Unknown')}",
            )

            if audit_id:
                with st.spinner("Loading details..."):
                    try:
                        detail_response = httpx.get(
                            f"{API_URL}/explain/{audit_id}",
                            timeout=30.0,
                        )

                        if detail_response.status_code == 200:
                            detail = detail_response.json()

                            # Display details
                            with st.expander("Classification Details", expanded=True):
                                col_a, col_b = st.columns(2)
                                with col_a:
                                    st.write(f"**Product:** {detail.get('product', {}).get('product_name')}")
                                    st.write(f"**Eligible:** {'Yes' if detail.get('classification', {}).get('is_ebt_eligible') else 'No'}")
                                with col_b:
                                    st.write(f"**Category:** {detail.get('classification', {}).get('classification_category')}")
                                    st.write(f"**Confidence:** {detail.get('classification', {}).get('confidence_score', 0) * 100:.0f}%")

                            with st.expander("Reasoning Chain"):
                                for i, step in enumerate(detail.get("explanation", {}).get("reasoning_chain", []), 1):
                                    st.write(f"{i}. {step}")

                            with st.expander("Key Factors"):
                                for factor in detail.get("explanation", {}).get("key_factors", []):
                                    st.write(f"- {factor}")

                    except Exception as e:
                        st.error(f"Error loading details: {str(e)}")

        else:
            st.info("No records found matching the filters.")

    # Statistics
    st.markdown("---")
    st.subheader("Statistics")

    try:
        stats_response = httpx.get(f"{API_URL}/audit-trail/stats", timeout=10.0)
        if stats_response.status_code == 200:
            stats = stats_response.json()

            col_s1, col_s2, col_s3, col_s4 = st.columns(4)

            with col_s1:
                st.metric("Total Classifications", stats.get("total_classifications", 0))
            with col_s2:
                st.metric("Eligible", stats.get("eligible_count", 0))
            with col_s3:
                st.metric("Ineligible", stats.get("ineligible_count", 0))
            with col_s4:
                st.metric("Challenged", stats.get("challenged_count", 0))

    except Exception:
        pass  # Stats are optional


def render_session_history() -> None:
    """Render session-based history for cloud deployment."""
    st.caption("Classification history for this session")

    # Get history from session state
    history = st.session_state.get("classification_history", [])

    if not history:
        st.info("No classifications yet. Search for products and check their eligibility to build history.")
        return

    # Stats
    total = len(history)
    eligible = sum(1 for h in history if h.get("is_eligible"))
    ineligible = total - eligible

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total", total)
    with col2:
        st.metric("Eligible", eligible)
    with col3:
        st.metric("Ineligible", ineligible)

    st.markdown("---")

    # Build dataframe
    df_data = []
    for h in reversed(history):  # Most recent first
        df_data.append({
            "Time": h.get("timestamp", "")[:19] if h.get("timestamp") else "-",
            "Product": h.get("product_name", "Unknown"),
            "Status": "Eligible" if h.get("is_eligible") else "Ineligible",
            "Category": (h.get("category") or "").replace("_", " ").title(),
            "Price": f"${h.get('price'):.2f}" if h.get("price") else "-",
            "Store": h.get("price_source", "-"),
        })

    df = pd.DataFrame(df_data)

    # Style
    def highlight_status(val):
        if val == "Eligible":
            return "background-color: #FAF7F5; color: #D4A27C; font-weight: 600;"
        elif val == "Ineligible":
            return "background-color: #F5F5F4; color: #6B7280; font-weight: 600;"
        return ""

    styled_df = df.style.map(highlight_status, subset=["Status"])

    st.dataframe(styled_df, use_container_width=True, hide_index=True)

    # Clear button
    if st.button("Clear History"):
        st.session_state.classification_history = []
        st.rerun()
