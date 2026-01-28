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
    initial_sidebar_state="collapsed",
)

# Anthropic-style custom CSS
st.markdown("""
<style>
    /* Import Inter font */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

    /* Hide Streamlit branding and menu */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    .stDeployButton {display: none;}

    /* Hide sidebar completely */
    section[data-testid="stSidebar"] {display: none;}
    .css-1d391kg {display: none;}
    [data-testid="collapsedControl"] {display: none;}

    /* Global styles */
    .stApp {
        background-color: #FAFAF9;
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
        color: #1A1A1A;
    }

    /* Main content area */
    .main .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
        max-width: 1200px;
    }

    /* Tab styling - Button style */
    .stTabs [data-baseweb="tab-list"] {
        gap: 12px;
        background-color: #F0EFED;
        border-radius: 12px;
        padding: 6px;
        border-bottom: none;
    }

    .stTabs [data-baseweb="tab"] {
        height: 44px;
        padding: 0 28px;
        background-color: transparent;
        border: none;
        border-radius: 8px;
        color: #666666;
        font-weight: 500;
        font-size: 15px;
        transition: all 0.2s ease;
    }

    .stTabs [data-baseweb="tab"]:hover {
        color: #1A1A1A;
        background-color: rgba(255, 255, 255, 0.5);
    }

    .stTabs [aria-selected="true"] {
        color: #1A1A1A !important;
        background-color: #FFFFFF !important;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
        font-weight: 600;
    }

    .stTabs [data-baseweb="tab-highlight"] {
        display: none;
    }

    .stTabs [data-baseweb="tab-border"] {
        display: none;
    }

    /* Button styling */
    .stButton > button {
        background-color: #D4A27C;
        color: #1A1A1A;
        border: none;
        border-radius: 6px;
        padding: 0.5rem 1.5rem;
        font-weight: 500;
        font-family: 'Inter', sans-serif;
        transition: all 0.2s ease;
    }

    .stButton > button:hover {
        background-color: #C4926C;
        border: none;
    }

    .stButton > button:active {
        background-color: #B4825C;
    }

    /* Form and input styling */
    .stTextInput > div > div > input,
    .stTextArea > div > div > textarea,
    .stSelectbox > div > div > div {
        border: 1px solid #E5E5E3;
        border-radius: 6px;
        font-family: 'Inter', sans-serif;
        background-color: #FFFFFF;
    }

    .stTextInput > div > div > input:focus,
    .stTextArea > div > div > textarea:focus {
        border-color: #D4A27C;
        box-shadow: 0 0 0 1px #D4A27C;
    }

    /* Card-like containers */
    .stForm {
        background-color: #FFFFFF;
        padding: 1.5rem;
        border-radius: 8px;
        border: 1px solid #E5E5E3;
    }

    /* Expander styling */
    .streamlit-expanderHeader {
        font-size: 14px;
        font-weight: 500;
        color: #1A1A1A;
        background-color: #FFFFFF;
        border-radius: 6px;
    }

    /* Headers */
    h1, h2, h3, h4, h5, h6 {
        font-family: 'Inter', sans-serif;
        color: #1A1A1A;
        font-weight: 600;
    }

    /* Success/Error messages */
    .stSuccess {
        background-color: #F0F9F4;
        border: 1px solid #86EFAC;
        border-radius: 6px;
    }

    .stError {
        background-color: #FEF2F2;
        border: 1px solid #FECACA;
        border-radius: 6px;
    }

    .stWarning {
        background-color: #FFFBEB;
        border: 1px solid #FDE68A;
        border-radius: 6px;
    }

    .stInfo {
        background-color: #F0F9FF;
        border: 1px solid #BAE6FD;
        border-radius: 6px;
    }

    /* Dataframe styling */
    .stDataFrame {
        border: 1px solid #E5E5E3;
        border-radius: 6px;
    }

    /* File uploader */
    .stFileUploader > div {
        border: 1px dashed #E5E5E3;
        border-radius: 6px;
        background-color: #FFFFFF;
    }

    .stFileUploader > div:hover {
        border-color: #D4A27C;
    }

    /* Metric styling */
    [data-testid="stMetricValue"] {
        font-family: 'Inter', sans-serif;
        color: #1A1A1A;
    }

    /* Link styling */
    a {
        color: #D4A27C;
    }

    a:hover {
        color: #C4926C;
    }

    /* Spinner */
    .stSpinner > div {
        border-top-color: #D4A27C !important;
    }

    /* Progress bar */
    .stProgress > div > div > div {
        background-color: #D4A27C;
    }

    /* Checkbox and radio */
    .stCheckbox label span,
    .stRadio label span {
        font-family: 'Inter', sans-serif;
    }

    /* Divider */
    hr {
        border-color: #E5E5E3;
    }

    /* Caption text */
    .stCaption {
        color: #666666;
    }
</style>
""", unsafe_allow_html=True)

# Banner with team name and app description
st.markdown("""
<div style="
    background: linear-gradient(135deg, #1A1A1A 0%, #2D2D2D 100%);
    border-radius: 16px;
    padding: 1.5rem 2rem;
    margin-bottom: 1.5rem;
    display: flex;
    justify-content: space-between;
    align-items: center;
">
    <div>
        <div style="
            font-size: 0.75rem;
            font-weight: 600;
            color: #D4A27C;
            letter-spacing: 1px;
            text-transform: uppercase;
            margin-bottom: 0.5rem;
        ">Team Classify</div>
        <div style="
            font-size: 1.5rem;
            font-weight: 700;
            color: #FFFFFF;
            margin-bottom: 0.25rem;
        ">EBT Eligibility Checker</div>
        <div style="
            font-size: 0.875rem;
            color: #9CA3AF;
        ">AI-powered SNAP classification with real-time pricing from Kroger, Walmart, Target & more</div>
    </div>
    <div style="
        display: flex;
        gap: 0.75rem;
    ">
        <div style="
            background: rgba(212, 162, 124, 0.15);
            border: 1px solid rgba(212, 162, 124, 0.3);
            border-radius: 8px;
            padding: 0.5rem 1rem;
            text-align: center;
        ">
            <div style="font-size: 0.625rem; color: #9CA3AF; text-transform: uppercase;">Response</div>
            <div style="font-size: 1rem; font-weight: 600; color: #D4A27C;">&lt;500ms</div>
        </div>
        <div style="
            background: rgba(212, 162, 124, 0.15);
            border: 1px solid rgba(212, 162, 124, 0.3);
            border-radius: 8px;
            padding: 0.5rem 1rem;
            text-align: center;
        ">
            <div style="font-size: 0.625rem; color: #9CA3AF; text-transform: uppercase;">Sources</div>
            <div style="font-size: 1rem; font-weight: 600; color: #D4A27C;">5+ Stores</div>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# App header
col_title, col_settings = st.columns([4, 1])

with col_title:
    st.markdown("")  # Spacing only - title is in banner

with col_settings:
    st.markdown("")
    with st.popover("Settings", use_container_width=True):
        st.markdown("**LLM Provider**")

        # Initialize session state for LLM mode
        if "llm_mode" not in st.session_state:
            st.session_state.llm_mode = "local"
        if "ollama_cloud_key" not in st.session_state:
            # Try to load from Streamlit secrets first
            try:
                if hasattr(st, "secrets") and "OLLAMA_CLOUD_API_KEY" in st.secrets:
                    st.session_state.ollama_cloud_key = st.secrets["OLLAMA_CLOUD_API_KEY"]
                    st.session_state.ollama_cloud_base_url = st.secrets.get("OLLAMA_CLOUD_BASE_URL", "https://ollama.com")
                    st.session_state.ollama_cloud_model = st.secrets.get("OLLAMA_MODEL", "ministral-3:3b:cloud")
                else:
                    st.session_state.ollama_cloud_key = ""
                    st.session_state.ollama_cloud_base_url = "https://ollama.com"
                    st.session_state.ollama_cloud_model = "ministral-3:3b:cloud"
            except Exception:
                st.session_state.ollama_cloud_key = ""
                st.session_state.ollama_cloud_base_url = "https://ollama.com"
                st.session_state.ollama_cloud_model = "ministral-3:3b:cloud"
        if "api_key_saved" not in st.session_state:
            # Auto-mark as saved if loaded from secrets
            st.session_state.api_key_saved = bool(st.session_state.ollama_cloud_key)

        llm_mode = st.radio(
            "Select mode",
            options=["local", "cloud"],
            format_func=lambda x: "Local Ollama" if x == "local" else "Cloud LLM",
            key="llm_mode_radio",
            label_visibility="collapsed",
        )

        if llm_mode != st.session_state.llm_mode:
            st.session_state.llm_mode = llm_mode

        if llm_mode == "cloud":
            st.markdown("")

            # Check if API key is available from secrets
            has_secret_key = bool(st.session_state.ollama_cloud_key)

            if has_secret_key:
                st.success("API key loaded from secrets")
            else:
                api_key = st.text_input(
                    "Cloud API Key",
                    type="password",
                    value="",
                    placeholder="Enter your API key",
                    help="API key for cloud LLM provider",
                    key="api_key_input",
                )

                if st.button("Save Key", key="save_api_key", use_container_width=True):
                    if api_key:
                        st.session_state.ollama_cloud_key = api_key
                        st.session_state.api_key_saved = True
                        st.rerun()

                if st.session_state.api_key_saved and st.session_state.ollama_cloud_key:
                    st.success("Key saved for session")

            model_name = st.session_state.get("ollama_cloud_model", "llama3.2:3b")
            st.caption(f"Model: {model_name}")
        else:
            st.caption("Using local Ollama at localhost:11434")

        st.markdown("---")
        st.caption(f"Mode: **{llm_mode.title()}**")

# Tab navigation
tab1, tab2, tab3 = st.tabs(["Check Eligibility", "Bulk Upload", "History"])

with tab1:
    from ui.pages.classify import render_classify_page
    render_classify_page()

with tab2:
    from ui.pages.bulk_upload import render_bulk_page
    render_bulk_page()

with tab3:
    from ui.pages.audit_viewer import render_audit_page
    render_audit_page()

# Footer with HTC logo
import base64
from pathlib import Path

# Load and encode the HTC logo
logo_path = Path(__file__).parent / "htc_logo.webp"
if logo_path.exists():
    with open(logo_path, "rb") as f:
        logo_base64 = base64.b64encode(f.read()).decode()

    st.markdown("""
    <div style="
        margin-top: 3rem;
        padding: 1.5rem 0;
        border-top: 1px solid #E5E5E3;
        display: flex;
        justify-content: center;
        align-items: center;
        gap: 1rem;
    ">
        <span style="color: #9CA3AF; font-size: 0.875rem;">Powered by</span>
        <img src="data:image/webp;base64,{}" style="height: 32px; opacity: 0.8;" alt="HTC">
    </div>
    """.format(logo_base64), unsafe_allow_html=True)
else:
    st.markdown("""
    <div style="
        margin-top: 3rem;
        padding: 1.5rem 0;
        border-top: 1px solid #E5E5E3;
        text-align: center;
        color: #9CA3AF;
        font-size: 0.875rem;
    ">
        Powered by HTC
    </div>
    """, unsafe_allow_html=True)
