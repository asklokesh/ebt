"""
Streamlit UI for EBT Eligibility Classification.
"""

import sys
from pathlib import Path

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

import streamlit as st

st.set_page_config(
    page_title="EBT Eligibility Checker",
    page_icon=None,
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS for cleaner UI
st.markdown("""
<style>
    /* Cleaner header */
    .stApp header {
        background-color: transparent;
    }

    /* Better button styling */
    .stButton > button {
        border-radius: 8px;
    }

    /* Cleaner expander */
    .streamlit-expanderHeader {
        font-size: 14px;
    }

    /* Better form styling */
    .stForm {
        padding: 1rem;
        border-radius: 8px;
        border: 1px solid #e0e0e0;
    }

    /* Sidebar styling */
    section[data-testid="stSidebar"] {
        width: 280px !important;
    }

    /* Hide hamburger menu */
    #MainMenu {visibility: hidden;}

    /* Footer styling */
    footer {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# Sidebar navigation
st.sidebar.title("EBT Eligibility Checker")
st.sidebar.caption("SNAP/EBT Product Classification")
st.sidebar.markdown("---")

# Navigation
page = st.sidebar.radio(
    "Menu",
    [
        "Check Eligibility",
        "Bulk Upload",
        "History",
        "Challenge",
    ],
    label_visibility="collapsed",
)

# Render selected page
if page == "Check Eligibility":
    from ui.pages.classify import render_classify_page
    render_classify_page()

elif page == "Bulk Upload":
    from ui.pages.bulk_upload import render_bulk_page
    render_bulk_page()

elif page == "History":
    from ui.pages.audit_viewer import render_audit_page
    render_audit_page()

elif page == "Challenge":
    from ui.pages.challenge import render_challenge_page
    render_challenge_page()


# Footer info
st.sidebar.markdown("---")
st.sidebar.markdown("""
**About**

Based on USDA SNAP regulations (7 CFR 271.2)

**Data Sources**
- USDA FoodData Central
- Open Food Facts
""")

st.sidebar.markdown("---")
st.sidebar.caption("v1.0.0")
