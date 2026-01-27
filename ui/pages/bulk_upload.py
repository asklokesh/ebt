"""Bulk upload and classification page with clean Anthropic-style design."""

import csv
import io
import streamlit as st
import httpx
import os
import pandas as pd
from typing import List, Dict, Any


# API URL from environment or default
API_URL = os.environ.get("API_URL", "http://localhost:8000")


def parse_csv_products(csv_content: str) -> List[Dict[str, Any]]:
    """
    Parse CSV content into product dicts.

    Args:
        csv_content: CSV file content as string

    Returns:
        List of product dicts
    """
    products = []
    reader = csv.DictReader(io.StringIO(csv_content))

    for row in reader:
        product = {
            "product_id": row.get("product_id") or row.get("id") or row.get("sku"),
            "product_name": row.get("product_name") or row.get("name"),
            "category": row.get("category"),
            "brand": row.get("brand"),
            "upc": row.get("upc") or row.get("barcode"),
            "description": row.get("description"),
            "nutrition_label_type": row.get("nutrition_label_type") or row.get("label_type"),
        }

        # Handle boolean fields
        if row.get("is_hot_at_sale"):
            product["is_hot_at_sale"] = row["is_hot_at_sale"].lower() in ("true", "yes", "1")
        if row.get("contains_tobacco"):
            product["contains_tobacco"] = row["contains_tobacco"].lower() in ("true", "yes", "1")

        # Handle alcohol content
        if row.get("alcohol_content"):
            try:
                product["alcohol_content"] = float(row["alcohol_content"])
            except ValueError:
                pass

        # Filter out None values for required fields
        if product["product_id"] and product["product_name"]:
            products.append(product)

    return products


def render_bulk_page() -> None:
    """Render the bulk upload page with clean Anthropic-style design."""
    st.title("Bulk Classification")
    st.caption("Upload a CSV file to classify multiple products at once")

    # Custom CSS for this page
    st.markdown("""
    <style>
        /* File uploader styling */
        .stFileUploader > div > div {
            border: 2px dashed #D4D4D4;
            border-radius: 12px;
            padding: 2rem;
            background-color: #FAFAFA;
        }
        .stFileUploader > div > div:hover {
            border-color: #10A37F;
            background-color: #F9FDFB;
        }

        /* Stats card styling */
        .stat-card {
            background: white;
            border: 1px solid #E5E5E5;
            border-radius: 12px;
            padding: 1.5rem;
            text-align: center;
        }
        .stat-value {
            font-size: 2rem;
            font-weight: 600;
            color: #171717;
            line-height: 1;
        }
        .stat-label {
            font-size: 0.875rem;
            color: #737373;
            margin-top: 0.5rem;
        }

        /* Eligible badge */
        .badge-eligible {
            display: inline-block;
            background-color: #10A37F;
            color: white;
            padding: 4px 12px;
            border-radius: 9999px;
            font-size: 0.75rem;
            font-weight: 600;
        }

        /* Ineligible badge */
        .badge-ineligible {
            display: inline-block;
            background-color: #EF4444;
            color: white;
            padding: 4px 12px;
            border-radius: 9999px;
            font-size: 0.75rem;
            font-weight: 600;
        }
    </style>
    """, unsafe_allow_html=True)

    # File upload section
    st.markdown("### Upload CSV")

    uploaded_file = st.file_uploader(
        "Drop your CSV file here or click to browse",
        type=["csv"],
        help="CSV should include product_id and product_name columns",
        label_visibility="collapsed",
    )

    # CSV format helper
    with st.expander("View expected CSV format"):
        st.markdown("""
        **Required columns:**
        - `product_id` - Unique identifier (or `id`, `sku`)
        - `product_name` - Product name (or `name`)

        **Optional columns:**
        - `category` - Product category
        - `brand` - Brand name
        - `upc` - Barcode (or `barcode`)
        - `description` - Product description
        - `nutrition_label_type` - "nutrition_facts", "supplement_facts", or "none"
        - `is_hot_at_sale` - true/false
        - `alcohol_content` - Decimal (e.g., 0.05 for 5%)
        - `contains_tobacco` - true/false
        """)

        example_csv = """product_id,product_name,category,nutrition_label_type
SKU-001,Fresh Apples,Produce,nutrition_facts
SKU-002,Monster Energy,Beverages,nutrition_facts
SKU-003,Budweiser Beer,Alcohol,none
SKU-004,Centrum Vitamin,Health,supplement_facts"""
        st.code(example_csv, language="csv")

    # Process uploaded file
    if uploaded_file is not None:
        csv_content = uploaded_file.read().decode("utf-8")
        products = parse_csv_products(csv_content)

        if len(products) == 0:
            st.error("No valid products found. Check that your CSV has product_id and product_name columns.")
            return

        st.markdown(f"**{len(products)} products** ready for classification")

        if st.button("Classify All Products", type="primary", use_container_width=True):
            process_bulk_classification(products)


def process_bulk_classification(products: List[Dict[str, Any]]) -> None:
    """Process bulk classification and display results."""
    with st.spinner(f"Classifying {len(products)} products..."):
        try:
            response = httpx.post(
                f"{API_URL}/classify/bulk",
                json={
                    "products": products,
                    "options": {
                        "parallel_processing": True,
                        "max_concurrent": 5,
                        "fail_fast": False,
                    },
                },
                timeout=300.0,
            )

            if response.status_code == 200:
                result = response.json()
                render_results(result)
            else:
                st.error(f"API Error: {response.status_code}")
                st.json(response.json())

        except httpx.ConnectError:
            st.error("Could not connect to the API. Make sure the API server is running.")
        except Exception as e:
            st.error(f"Error: {str(e)}")


def render_results(result: Dict[str, Any]) -> None:
    """Render classification results with clean styling."""
    results = result.get("results", [])
    total = result.get("total_products", 0)
    successful = result.get("successful", 0)
    failed = result.get("failed", 0)

    # Calculate eligibility stats
    eligible_count = sum(1 for r in results if r.get("is_ebt_eligible", False))
    ineligible_count = len(results) - eligible_count

    # Summary stats
    st.markdown("---")
    st.markdown("### Summary")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.markdown(f"""
        <div class="stat-card">
            <div class="stat-value">{total}</div>
            <div class="stat-label">Total Products</div>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown(f"""
        <div class="stat-card">
            <div class="stat-value" style="color: #10A37F;">{eligible_count}</div>
            <div class="stat-label">Eligible</div>
        </div>
        """, unsafe_allow_html=True)

    with col3:
        st.markdown(f"""
        <div class="stat-card">
            <div class="stat-value" style="color: #EF4444;">{ineligible_count}</div>
            <div class="stat-label">Ineligible</div>
        </div>
        """, unsafe_allow_html=True)

    with col4:
        success_rate = (successful / total * 100) if total > 0 else 0
        st.markdown(f"""
        <div class="stat-card">
            <div class="stat-value">{success_rate:.0f}%</div>
            <div class="stat-label">Success Rate</div>
        </div>
        """, unsafe_allow_html=True)

    # Results table
    if results:
        st.markdown("---")
        st.markdown("### Results")

        # Build dataframe
        df_data = []
        for r in results:
            is_eligible = r.get("is_ebt_eligible", False)
            df_data.append({
                "Product ID": r.get("product_id", ""),
                "Name": r.get("product_name", ""),
                "Status": "Eligible" if is_eligible else "Ineligible",
                "Category": r.get("classification_category", "").replace("_", " ").title(),
                "Confidence": f"{r.get('confidence_score', 0) * 100:.0f}%",
                "_eligible": is_eligible,  # Hidden column for styling
            })

        df = pd.DataFrame(df_data)

        # Apply row styling based on eligibility
        def style_row(row):
            if row["_eligible"]:
                return ["background-color: #ECFDF5"] * len(row)
            else:
                return ["background-color: #FEF2F2"] * len(row)

        # Apply badge styling to Status column
        def style_status(val):
            if val == "Eligible":
                return "background-color: #10A37F; color: white; font-weight: 600; border-radius: 9999px; padding: 2px 8px;"
            else:
                return "background-color: #EF4444; color: white; font-weight: 600; border-radius: 9999px; padding: 2px 8px;"

        # Style confidence based on value
        def style_confidence(val):
            try:
                pct = int(val.replace("%", ""))
                if pct >= 90:
                    return "color: #10A37F; font-weight: 600;"
                elif pct >= 70:
                    return "color: #F59E0B; font-weight: 600;"
                else:
                    return "color: #EF4444; font-weight: 600;"
            except (ValueError, AttributeError):
                return ""

        # Display columns (hide _eligible)
        display_df = df[["Product ID", "Name", "Status", "Category", "Confidence"]]

        styled_df = display_df.style.apply(
            lambda row: style_row(df.loc[row.name]), axis=1
        ).map(
            style_status, subset=["Status"]
        ).map(
            style_confidence, subset=["Confidence"]
        )

        st.dataframe(
            styled_df,
            width="stretch",
            height=min(400, 56 + len(df_data) * 35),
            hide_index=True,
        )

        # Download button
        st.markdown("")
        csv_buffer = io.StringIO()
        display_df.to_csv(csv_buffer, index=False)
        st.download_button(
            label="Download Results as CSV",
            data=csv_buffer.getvalue(),
            file_name="ebt_classification_results.csv",
            mime="text/csv",
        )

    # Show errors if any
    if result.get("errors"):
        st.markdown("---")
        st.markdown("### Errors")
        for error in result["errors"]:
            st.error(str(error))
