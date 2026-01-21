"""Classification result display component."""

import streamlit as st
from typing import Dict, Any


def render_result_display(result: Dict[str, Any]) -> None:
    """
    Render the classification result.

    Args:
        result: Classification result dict
    """
    is_eligible = result.get("is_ebt_eligible", False)
    confidence = result.get("confidence_score", 0)
    category = result.get("classification_category", "UNKNOWN")

    # Main result badge
    col1, col2, col3 = st.columns([2, 1, 1])

    with col1:
        if is_eligible:
            st.success(f"## ELIGIBLE")
            st.caption(f"Category: {category.replace('_', ' ')}")
        else:
            st.error(f"## INELIGIBLE")
            st.caption(f"Reason: {category.replace('_', ' ')}")

    with col2:
        st.metric(
            label="Confidence",
            value=f"{confidence * 100:.0f}%",
            delta=None,
        )

    with col3:
        processing_time = result.get("processing_time_ms", 0)
        st.metric(
            label="Processing Time",
            value=f"{processing_time}ms",
            delta=None,
        )

    st.markdown("---")

    # Product info
    st.subheader("Product")
    col_a, col_b = st.columns(2)
    with col_a:
        st.write(f"**ID:** {result.get('product_id', 'N/A')}")
    with col_b:
        st.write(f"**Name:** {result.get('product_name', 'N/A')}")

    # Audit info
    st.subheader("Audit")
    col_c, col_d = st.columns(2)
    with col_c:
        st.write(f"**Audit ID:** `{result.get('audit_id', 'N/A')}`")
    with col_d:
        st.write(f"**Timestamp:** {result.get('classification_timestamp', 'N/A')}")


def render_confidence_gauge(confidence: float) -> None:
    """
    Render a confidence score gauge.

    Args:
        confidence: Confidence score (0-1)
    """
    percentage = confidence * 100

    # Color based on confidence level
    if percentage >= 90:
        color = "green"
        label = "High"
    elif percentage >= 70:
        color = "orange"
        label = "Medium"
    else:
        color = "red"
        label = "Low"

    st.markdown(f"""
    <div style="text-align: center;">
        <div style="font-size: 48px; font-weight: bold; color: {color};">
            {percentage:.0f}%
        </div>
        <div style="font-size: 14px; color: gray;">
            {label} Confidence
        </div>
    </div>
    """, unsafe_allow_html=True)


def render_eligibility_summary(results: list) -> None:
    """
    Render a summary of bulk classification results.

    Args:
        results: List of classification results
    """
    total = len(results)
    eligible = sum(1 for r in results if r.get("is_ebt_eligible", False))
    ineligible = total - eligible
    low_confidence = sum(1 for r in results if r.get("confidence_score", 1) < 0.8)

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Total", total)
    with col2:
        st.metric("Eligible", eligible, delta=None)
    with col3:
        st.metric("Ineligible", ineligible, delta=None)
    with col4:
        st.metric("Low Confidence", low_confidence, delta=None)
