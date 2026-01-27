"""Classification result display component with Anthropic design."""

import streamlit as st
from typing import Dict, Any


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


def render_result_display(result: Dict[str, Any]) -> None:
    """
    Render the classification result with clean card design.

    Args:
        result: Classification result dict
    """
    is_eligible = result.get("is_ebt_eligible", False)
    confidence = result.get("confidence_score", 0)
    category = result.get("classification_category", "UNKNOWN")
    processing_time = result.get("processing_time_ms", 0)

    # Result card container
    badge_color = COLORS["success"] if is_eligible else COLORS["error"]
    badge_text = "ELIGIBLE" if is_eligible else "INELIGIBLE"

    st.markdown(f"""
    <style>
        .result-card {{
            background: white;
            border: 1px solid {COLORS["border"]};
            border-radius: 12px;
            padding: 24px;
            margin-bottom: 16px;
            box-shadow: 0 1px 3px rgba(0, 0, 0, 0.04);
        }}
        .result-badge {{
            display: inline-block;
            background: {badge_color};
            color: white;
            font-family: Inter, -apple-system, BlinkMacSystemFont, sans-serif;
            font-size: 14px;
            font-weight: 600;
            letter-spacing: 0.5px;
            padding: 6px 16px;
            border-radius: 6px;
        }}
        .result-category {{
            color: {COLORS["text_muted"]};
            font-family: Inter, -apple-system, BlinkMacSystemFont, sans-serif;
            font-size: 13px;
            margin-top: 8px;
        }}
        .metrics-row {{
            display: flex;
            gap: 32px;
            margin-top: 20px;
            padding-top: 20px;
            border-top: 1px solid {COLORS["border"]};
        }}
        .metric-item {{
            text-align: left;
        }}
        .metric-label {{
            color: {COLORS["text_muted"]};
            font-family: Inter, -apple-system, BlinkMacSystemFont, sans-serif;
            font-size: 12px;
            font-weight: 500;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            margin-bottom: 4px;
        }}
        .metric-value {{
            color: {COLORS["text"]};
            font-family: Inter, -apple-system, BlinkMacSystemFont, sans-serif;
            font-size: 20px;
            font-weight: 600;
        }}
    </style>
    <div class="result-card">
        <span class="result-badge">{badge_text}</span>
        <div class="result-category">{category.replace('_', ' ').title()}</div>
        <div class="metrics-row">
            <div class="metric-item">
                <div class="metric-label">Confidence</div>
                <div class="metric-value">{confidence * 100:.0f}%</div>
            </div>
            <div class="metric-item">
                <div class="metric-label">Processing</div>
                <div class="metric-value">{processing_time}ms</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Product info card
    product_id = result.get("product_id", "N/A")
    product_name = result.get("product_name", "N/A")

    st.markdown(f"""
    <style>
        .info-card {{
            background: {COLORS["background"]};
            border: 1px solid {COLORS["border"]};
            border-radius: 8px;
            padding: 16px 20px;
            margin-bottom: 12px;
        }}
        .info-label {{
            color: {COLORS["text_muted"]};
            font-family: Inter, -apple-system, BlinkMacSystemFont, sans-serif;
            font-size: 12px;
            font-weight: 500;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            margin-bottom: 4px;
        }}
        .info-value {{
            color: {COLORS["text"]};
            font-family: Inter, -apple-system, BlinkMacSystemFont, sans-serif;
            font-size: 14px;
        }}
        .info-row {{
            display: flex;
            gap: 40px;
        }}
        .info-item {{
            flex: 1;
        }}
    </style>
    <div class="info-card">
        <div class="info-row">
            <div class="info-item">
                <div class="info-label">Product ID</div>
                <div class="info-value">{product_id}</div>
            </div>
            <div class="info-item">
                <div class="info-label">Product Name</div>
                <div class="info-value">{product_name}</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)


def render_confidence_gauge(confidence: float) -> None:
    """
    Render a minimal confidence indicator.

    Args:
        confidence: Confidence score (0-1)
    """
    percentage = confidence * 100

    if percentage >= 90:
        color = COLORS["success"]
        label = "High"
    elif percentage >= 70:
        color = COLORS["primary"]
        label = "Medium"
    else:
        color = COLORS["error"]
        label = "Low"

    st.markdown(f"""
    <style>
        .confidence-display {{
            text-align: center;
            padding: 20px;
        }}
        .confidence-value {{
            font-family: Inter, -apple-system, BlinkMacSystemFont, sans-serif;
            font-size: 42px;
            font-weight: 600;
            color: {color};
            line-height: 1;
        }}
        .confidence-label {{
            font-family: Inter, -apple-system, BlinkMacSystemFont, sans-serif;
            font-size: 13px;
            color: {COLORS["text_muted"]};
            margin-top: 8px;
        }}
    </style>
    <div class="confidence-display">
        <div class="confidence-value">{percentage:.0f}%</div>
        <div class="confidence-label">{label} Confidence</div>
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

    st.markdown(f"""
    <style>
        .summary-grid {{
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 16px;
            margin: 16px 0;
        }}
        .summary-card {{
            background: white;
            border: 1px solid {COLORS["border"]};
            border-radius: 8px;
            padding: 16px;
            text-align: center;
        }}
        .summary-value {{
            font-family: Inter, -apple-system, BlinkMacSystemFont, sans-serif;
            font-size: 28px;
            font-weight: 600;
            color: {COLORS["text"]};
        }}
        .summary-label {{
            font-family: Inter, -apple-system, BlinkMacSystemFont, sans-serif;
            font-size: 12px;
            color: {COLORS["text_muted"]};
            text-transform: uppercase;
            letter-spacing: 0.5px;
            margin-top: 4px;
        }}
        .summary-eligible .summary-value {{
            color: {COLORS["success"]};
        }}
        .summary-ineligible .summary-value {{
            color: {COLORS["error"]};
        }}
        .summary-warning .summary-value {{
            color: {COLORS["primary"]};
        }}
    </style>
    <div class="summary-grid">
        <div class="summary-card">
            <div class="summary-value">{total}</div>
            <div class="summary-label">Total</div>
        </div>
        <div class="summary-card summary-eligible">
            <div class="summary-value">{eligible}</div>
            <div class="summary-label">Eligible</div>
        </div>
        <div class="summary-card summary-ineligible">
            <div class="summary-value">{ineligible}</div>
            <div class="summary-label">Ineligible</div>
        </div>
        <div class="summary-card summary-warning">
            <div class="summary-value">{low_confidence}</div>
            <div class="summary-label">Low Confidence</div>
        </div>
    </div>
    """, unsafe_allow_html=True)
