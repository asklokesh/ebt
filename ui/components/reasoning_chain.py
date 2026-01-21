"""Reasoning chain display component."""

import streamlit as st
from typing import Dict, Any, List


def render_reasoning_chain(result: Dict[str, Any]) -> None:
    """
    Render the reasoning chain from a classification result.

    Args:
        result: Classification result dict
    """
    reasoning = result.get("reasoning_chain", [])
    key_factors = result.get("key_factors", [])
    citations = result.get("regulation_citations", [])

    # Reasoning steps
    with st.expander("Reasoning Chain", expanded=True):
        if reasoning:
            for i, step in enumerate(reasoning, 1):
                st.markdown(f"**{i}.** {step}")
        else:
            st.info("No reasoning steps available.")

    # Key factors
    with st.expander("Key Factors", expanded=False):
        if key_factors:
            for factor in key_factors:
                st.markdown(f"- {factor}")
        else:
            st.info("No key factors identified.")

    # Citations
    with st.expander("Regulation Citations", expanded=False):
        if citations:
            for citation in citations:
                if isinstance(citation, dict):
                    st.markdown(f"**{citation.get('regulation_id', 'Unknown')}**")
                    st.markdown(f"*Section:* {citation.get('section', 'N/A')}")
                    st.markdown(f"> {citation.get('excerpt', 'No excerpt')}")
                    if citation.get("source_url"):
                        st.markdown(f"[Source]({citation.get('source_url')})")
                    st.markdown("---")
        else:
            st.info("No citations available.")

    # Data sources
    data_sources = result.get("data_sources_used", [])
    if data_sources:
        with st.expander("Data Sources Used", expanded=False):
            for source in data_sources:
                st.markdown(f"- {source}")


def render_comparison(original: Dict[str, Any], new: Dict[str, Any]) -> None:
    """
    Render a side-by-side comparison of two classifications.

    Args:
        original: Original classification result
        new: New classification result (after challenge)
    """
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Original Classification")
        is_eligible = original.get("is_ebt_eligible", False)
        if is_eligible:
            st.success("ELIGIBLE")
        else:
            st.error("INELIGIBLE")

        st.write(f"**Category:** {original.get('classification_category', 'N/A')}")
        st.write(f"**Confidence:** {original.get('confidence_score', 0) * 100:.0f}%")

    with col2:
        st.subheader("New Classification")
        is_eligible = new.get("is_ebt_eligible", False)
        if is_eligible:
            st.success("ELIGIBLE")
        else:
            st.error("INELIGIBLE")

        st.write(f"**Category:** {new.get('classification_category', 'N/A')}")
        st.write(f"**Confidence:** {new.get('confidence_score', 0) * 100:.0f}%")

    # Highlight changes
    original_eligible = original.get("is_ebt_eligible")
    new_eligible = new.get("is_ebt_eligible")

    if original_eligible != new_eligible:
        st.warning("Classification CHANGED based on new evidence.")
    else:
        st.info("Classification remains UNCHANGED.")


def render_timeline(events: List[Dict[str, Any]]) -> None:
    """
    Render a timeline of classification events.

    Args:
        events: List of events with timestamp and description
    """
    st.subheader("Classification Timeline")

    for event in events:
        timestamp = event.get("timestamp", "Unknown")
        description = event.get("description", "Event")
        event_type = event.get("type", "info")

        # Format based on event type
        if event_type == "challenge":
            icon = "!"
        elif event_type == "classification":
            icon = "*"
        else:
            icon = "-"

        st.markdown(f"**{timestamp}** {icon} {description}")
