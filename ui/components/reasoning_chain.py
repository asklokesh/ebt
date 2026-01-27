"""Reasoning chain display component with Anthropic design."""

import streamlit as st
from typing import Dict, Any, List


# Design tokens
COLORS = {
    "primary": "#D4A27C",
    "success": "#10A37F",
    "error": "#EF4444",
    "background": "#FAFAF9",
    "text": "#1A1A1A",
    "text_muted": "#6B7280",
    "border": "#E5E5E5",
}


def _inject_base_styles() -> None:
    """Inject base styles for reasoning components."""
    st.markdown(f"""
    <style>
        .section-card {{
            background: white;
            border: 1px solid {COLORS["border"]};
            border-radius: 10px;
            margin-bottom: 12px;
            overflow: hidden;
        }}
        .section-header {{
            background: {COLORS["background"]};
            padding: 14px 20px;
            border-bottom: 1px solid {COLORS["border"]};
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: space-between;
        }}
        .section-title {{
            font-family: Inter, -apple-system, BlinkMacSystemFont, sans-serif;
            font-size: 14px;
            font-weight: 600;
            color: {COLORS["text"]};
            margin: 0;
        }}
        .section-content {{
            padding: 16px 20px;
        }}
        .step-item {{
            display: flex;
            align-items: flex-start;
            margin-bottom: 12px;
            padding-bottom: 12px;
            border-bottom: 1px solid {COLORS["border"]};
        }}
        .step-item:last-child {{
            margin-bottom: 0;
            padding-bottom: 0;
            border-bottom: none;
        }}
        .step-number {{
            background: {COLORS["primary"]};
            color: white;
            font-family: Inter, -apple-system, BlinkMacSystemFont, sans-serif;
            font-size: 12px;
            font-weight: 600;
            width: 24px;
            height: 24px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            flex-shrink: 0;
            margin-right: 12px;
        }}
        .step-text {{
            font-family: Inter, -apple-system, BlinkMacSystemFont, sans-serif;
            font-size: 14px;
            line-height: 1.5;
            color: {COLORS["text"]};
        }}
        .factor-item {{
            font-family: Inter, -apple-system, BlinkMacSystemFont, sans-serif;
            font-size: 14px;
            line-height: 1.6;
            color: {COLORS["text"]};
            padding: 8px 0;
            padding-left: 16px;
            border-left: 2px solid {COLORS["primary"]};
            margin-bottom: 8px;
        }}
        .citation-card {{
            background: {COLORS["background"]};
            border-radius: 8px;
            padding: 14px 16px;
            margin-bottom: 10px;
        }}
        .citation-id {{
            font-family: Inter, -apple-system, BlinkMacSystemFont, sans-serif;
            font-size: 13px;
            font-weight: 600;
            color: {COLORS["text"]};
        }}
        .citation-section {{
            font-family: Inter, -apple-system, BlinkMacSystemFont, sans-serif;
            font-size: 12px;
            color: {COLORS["text_muted"]};
            margin-top: 4px;
        }}
        .citation-excerpt {{
            font-family: Inter, -apple-system, BlinkMacSystemFont, sans-serif;
            font-size: 13px;
            font-style: italic;
            color: {COLORS["text"]};
            margin-top: 10px;
            padding: 10px 12px;
            background: white;
            border-radius: 6px;
            border-left: 3px solid {COLORS["primary"]};
        }}
        .citation-link {{
            font-family: Inter, -apple-system, BlinkMacSystemFont, sans-serif;
            font-size: 12px;
            color: {COLORS["primary"]};
            text-decoration: none;
            margin-top: 8px;
            display: inline-block;
        }}
        .source-tag {{
            display: inline-block;
            background: {COLORS["background"]};
            border: 1px solid {COLORS["border"]};
            font-family: Inter, -apple-system, BlinkMacSystemFont, sans-serif;
            font-size: 12px;
            color: {COLORS["text_muted"]};
            padding: 4px 10px;
            border-radius: 4px;
            margin-right: 8px;
            margin-bottom: 8px;
        }}
        .empty-state {{
            font-family: Inter, -apple-system, BlinkMacSystemFont, sans-serif;
            font-size: 13px;
            color: {COLORS["text_muted"]};
            text-align: center;
            padding: 20px;
        }}
    </style>
    """, unsafe_allow_html=True)


def render_reasoning_chain(result: Dict[str, Any]) -> None:
    """
    Render the reasoning chain with clean expandable sections.

    Args:
        result: Classification result dict
    """
    _inject_base_styles()

    reasoning = result.get("reasoning_chain", [])
    key_factors = result.get("key_factors", [])
    citations = result.get("regulation_citations", [])
    data_sources = result.get("data_sources_used", [])

    # Reasoning steps
    with st.expander("Reasoning Chain", expanded=True):
        if reasoning:
            steps_html = ""
            for i, step in enumerate(reasoning, 1):
                steps_html += f"""
                <div class="step-item">
                    <div class="step-number">{i}</div>
                    <div class="step-text">{step}</div>
                </div>
                """
            st.markdown(f'<div>{steps_html}</div>', unsafe_allow_html=True)
        else:
            st.markdown('<div class="empty-state">No reasoning steps available</div>',
                       unsafe_allow_html=True)

    # Key factors
    with st.expander("Key Factors", expanded=False):
        if key_factors:
            factors_html = ""
            for factor in key_factors:
                factors_html += f'<div class="factor-item">{factor}</div>'
            st.markdown(factors_html, unsafe_allow_html=True)
        else:
            st.markdown('<div class="empty-state">No key factors identified</div>',
                       unsafe_allow_html=True)

    # Citations
    with st.expander("Regulation Citations", expanded=False):
        if citations:
            for citation in citations:
                if isinstance(citation, dict):
                    reg_id = citation.get("regulation_id", "Unknown")
                    section = citation.get("section", "N/A")
                    excerpt = citation.get("excerpt", "")
                    source_url = citation.get("source_url", "")

                    citation_html = f"""
                    <div class="citation-card">
                        <div class="citation-id">{reg_id}</div>
                        <div class="citation-section">Section: {section}</div>
                        {"<div class='citation-excerpt'>" + excerpt + "</div>" if excerpt else ""}
                        {"<a class='citation-link' href='" + source_url + "' target='_blank'>View Source</a>" if source_url else ""}
                    </div>
                    """
                    st.markdown(citation_html, unsafe_allow_html=True)
        else:
            st.markdown('<div class="empty-state">No citations available</div>',
                       unsafe_allow_html=True)

    # Data sources
    if data_sources:
        with st.expander("Data Sources", expanded=False):
            sources_html = ""
            for source in data_sources:
                sources_html += f'<span class="source-tag">{source}</span>'
            st.markdown(sources_html, unsafe_allow_html=True)


def render_comparison(original: Dict[str, Any], new: Dict[str, Any]) -> None:
    """
    Render a side-by-side comparison of two classifications.

    Args:
        original: Original classification result
        new: New classification result (after challenge)
    """
    _inject_base_styles()

    original_eligible = original.get("is_ebt_eligible", False)
    new_eligible = new.get("is_ebt_eligible", False)
    changed = original_eligible != new_eligible

    st.markdown(f"""
    <style>
        .comparison-grid {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 16px;
            margin-bottom: 16px;
        }}
        .comparison-card {{
            background: white;
            border: 1px solid {COLORS["border"]};
            border-radius: 10px;
            padding: 20px;
        }}
        .comparison-title {{
            font-family: Inter, -apple-system, BlinkMacSystemFont, sans-serif;
            font-size: 12px;
            font-weight: 500;
            color: {COLORS["text_muted"]};
            text-transform: uppercase;
            letter-spacing: 0.5px;
            margin-bottom: 12px;
        }}
        .comparison-badge {{
            display: inline-block;
            font-family: Inter, -apple-system, BlinkMacSystemFont, sans-serif;
            font-size: 13px;
            font-weight: 600;
            padding: 5px 12px;
            border-radius: 5px;
            color: white;
        }}
        .comparison-badge.eligible {{
            background: {COLORS["success"]};
        }}
        .comparison-badge.ineligible {{
            background: {COLORS["error"]};
        }}
        .comparison-detail {{
            font-family: Inter, -apple-system, BlinkMacSystemFont, sans-serif;
            font-size: 13px;
            color: {COLORS["text"]};
            margin-top: 12px;
        }}
        .comparison-detail strong {{
            color: {COLORS["text_muted"]};
            font-weight: 500;
        }}
        .change-notice {{
            background: {COLORS["background"]};
            border: 1px solid {COLORS["border"]};
            border-radius: 8px;
            padding: 12px 16px;
            font-family: Inter, -apple-system, BlinkMacSystemFont, sans-serif;
            font-size: 13px;
            color: {COLORS["text"]};
            text-align: center;
        }}
        .change-notice.changed {{
            border-color: {COLORS["primary"]};
            background: rgba(212, 162, 124, 0.1);
        }}
    </style>
    """, unsafe_allow_html=True)

    orig_badge_class = "eligible" if original_eligible else "ineligible"
    orig_badge_text = "ELIGIBLE" if original_eligible else "INELIGIBLE"
    new_badge_class = "eligible" if new_eligible else "ineligible"
    new_badge_text = "ELIGIBLE" if new_eligible else "INELIGIBLE"

    st.markdown(f"""
    <div class="comparison-grid">
        <div class="comparison-card">
            <div class="comparison-title">Original Classification</div>
            <span class="comparison-badge {orig_badge_class}">{orig_badge_text}</span>
            <div class="comparison-detail">
                <strong>Category:</strong> {original.get('classification_category', 'N/A')}
            </div>
            <div class="comparison-detail">
                <strong>Confidence:</strong> {original.get('confidence_score', 0) * 100:.0f}%
            </div>
        </div>
        <div class="comparison-card">
            <div class="comparison-title">New Classification</div>
            <span class="comparison-badge {new_badge_class}">{new_badge_text}</span>
            <div class="comparison-detail">
                <strong>Category:</strong> {new.get('classification_category', 'N/A')}
            </div>
            <div class="comparison-detail">
                <strong>Confidence:</strong> {new.get('confidence_score', 0) * 100:.0f}%
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    if changed:
        st.markdown("""
        <div class="change-notice changed">
            Classification changed based on new evidence
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div class="change-notice">
            Classification remains unchanged
        </div>
        """, unsafe_allow_html=True)


def render_timeline(events: List[Dict[str, Any]]) -> None:
    """
    Render a timeline of classification events.

    Args:
        events: List of events with timestamp and description
    """
    _inject_base_styles()

    st.markdown(f"""
    <style>
        .timeline-container {{
            padding: 16px 0;
        }}
        .timeline-item {{
            display: flex;
            align-items: flex-start;
            margin-bottom: 16px;
            position: relative;
        }}
        .timeline-marker {{
            width: 10px;
            height: 10px;
            border-radius: 50%;
            background: {COLORS["border"]};
            flex-shrink: 0;
            margin-top: 5px;
            margin-right: 16px;
        }}
        .timeline-marker.challenge {{
            background: {COLORS["primary"]};
        }}
        .timeline-marker.classification {{
            background: {COLORS["success"]};
        }}
        .timeline-content {{
            flex: 1;
        }}
        .timeline-time {{
            font-family: Inter, -apple-system, BlinkMacSystemFont, sans-serif;
            font-size: 12px;
            font-weight: 500;
            color: {COLORS["text_muted"]};
            margin-bottom: 4px;
        }}
        .timeline-desc {{
            font-family: Inter, -apple-system, BlinkMacSystemFont, sans-serif;
            font-size: 14px;
            color: {COLORS["text"]};
        }}
    </style>
    """, unsafe_allow_html=True)

    timeline_html = '<div class="timeline-container">'
    for event in events:
        timestamp = event.get("timestamp", "Unknown")
        description = event.get("description", "Event")
        event_type = event.get("type", "info")

        marker_class = event_type if event_type in ["challenge", "classification"] else ""

        timeline_html += f"""
        <div class="timeline-item">
            <div class="timeline-marker {marker_class}"></div>
            <div class="timeline-content">
                <div class="timeline-time">{timestamp}</div>
                <div class="timeline-desc">{description}</div>
            </div>
        </div>
        """

    timeline_html += '</div>'
    st.markdown(timeline_html, unsafe_allow_html=True)
