"""
Streamlit UI for EBT Eligibility Classification Demo.
"""

import sys
from pathlib import Path

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

import streamlit as st

st.set_page_config(
    page_title="EBT Eligibility Classifier",
    page_icon="",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Sidebar navigation
st.sidebar.title("EBT Eligibility Classifier")
st.sidebar.markdown("---")

page = st.sidebar.radio(
    "Navigation",
    ["Single Classification", "Bulk Upload", "Audit Trail", "Challenge Decision"],
)

if page == "Single Classification":
    from ui.pages.classify import render_classify_page
    render_classify_page()
elif page == "Bulk Upload":
    from ui.pages.bulk_upload import render_bulk_page
    render_bulk_page()
elif page == "Audit Trail":
    from ui.pages.audit_viewer import render_audit_page
    render_audit_page()
elif page == "Challenge Decision":
    from ui.pages.challenge import render_challenge_page
    render_challenge_page()

# Footer
st.sidebar.markdown("---")
st.sidebar.markdown("""
**Regulations:** 7 CFR 271.2

**Data Sources:** USDA, Open Food Facts

**Stack:** 100% Free Tier
""")

st.sidebar.markdown("---")
st.sidebar.caption("EBT Classification System v1.0.0")
