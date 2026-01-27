"""Bulk upload and classification page."""

import csv
import io
import streamlit as st
import httpx
import os
import pandas as pd
from typing import List, Dict, Any

from ui.components.result_display import render_eligibility_summary


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
    """Render the bulk upload page."""
    st.title("Bulk Classification")
    st.markdown(
        "Upload a CSV file to classify multiple products at once."
    )

    # File upload
    st.subheader("Upload CSV File")

    uploaded_file = st.file_uploader(
        "Choose a CSV file",
        type=["csv"],
        help="CSV should have columns: product_id, product_name, category, etc.",
    )

    # Show expected format
    with st.expander("Expected CSV Format"):
        st.markdown("""
        Your CSV should include these columns:
        - `product_id` (required): Unique identifier
        - `product_name` (required): Product name
        - `category`: Product category
        - `brand`: Brand name
        - `upc`: Barcode
        - `description`: Product description
        - `nutrition_label_type`: "nutrition_facts", "supplement_facts", or "none"
        - `is_hot_at_sale`: true/false
        - `alcohol_content`: decimal (e.g., 0.05 for 5%)
        - `contains_tobacco`: true/false
        """)

        st.markdown("**Example:**")
        example_csv = """product_id,product_name,category,nutrition_label_type,alcohol_content
SKU-001,Fresh Apples,Produce,nutrition_facts,0
SKU-002,Monster Energy,Beverages,nutrition_facts,0
SKU-003,Budweiser Beer,Beverages,,0.05
SKU-004,Centrum Vitamin,Health,supplement_facts,0"""
        st.code(example_csv, language="csv")

    # Processing options
    st.subheader("Processing Options")
    col1, col2 = st.columns(2)

    with col1:
        max_concurrent = st.slider(
            "Max Concurrent",
            min_value=1,
            max_value=10,
            value=5,
            help="Maximum concurrent API calls",
        )

    with col2:
        fail_fast = st.checkbox(
            "Stop on First Error",
            value=False,
            help="Stop processing if any product fails",
        )

    # Process button
    if uploaded_file is not None:
        csv_content = uploaded_file.read().decode("utf-8")
        products = parse_csv_products(csv_content)

        st.info(f"Found {len(products)} products in CSV file.")

        if st.button("Classify All Products", type="primary"):
            with st.spinner(f"Classifying {len(products)} products..."):
                try:
                    # Call bulk API
                    response = httpx.post(
                        f"{API_URL}/classify/bulk",
                        json={
                            "products": products,
                            "options": {
                                "parallel_processing": True,
                                "max_concurrent": max_concurrent,
                                "fail_fast": fail_fast,
                            },
                        },
                        timeout=300.0,  # 5 minute timeout for bulk
                    )

                    if response.status_code == 200:
                        result = response.json()

                        st.success("Classification complete!")

                        # Summary
                        st.markdown("---")
                        st.header("Summary")
                        render_eligibility_summary(result.get("results", []))

                        # Processing stats
                        st.markdown("---")
                        col_a, col_b, col_c = st.columns(3)
                        with col_a:
                            st.metric("Total Products", result.get("total_products", 0))
                        with col_b:
                            st.metric("Successful", result.get("successful", 0))
                        with col_c:
                            st.metric("Failed", result.get("failed", 0))

                        # Results table
                        st.markdown("---")
                        st.header("Results")

                        if result.get("results"):
                            df_data = []
                            for r in result["results"]:
                                df_data.append({
                                    "Product ID": r.get("product_id"),
                                    "Name": r.get("product_name"),
                                    "Eligible": "Yes" if r.get("is_ebt_eligible") else "No",
                                    "Category": r.get("classification_category", "").replace("_", " "),
                                    "Confidence": f"{r.get('confidence_score', 0) * 100:.0f}%",
                                    "Audit ID": r.get("audit_id", "")[:8] + "...",
                                })

                            df = pd.DataFrame(df_data)

                            # Apply row-level color styling based on eligibility
                            def color_row(row):
                                if row["Eligible"] == "Yes":
                                    return ["background-color: #d4edda"] * len(row)  # Light green
                                else:
                                    return ["background-color: #f8d7da"] * len(row)  # Light red

                            # Apply cell-level styling to Eligible column for emphasis
                            def color_eligible_cell(val):
                                if val == "Yes":
                                    return "background-color: #28a745; color: white; font-weight: bold"  # Dark green
                                else:
                                    return "background-color: #dc3545; color: white; font-weight: bold"  # Dark red

                            styled_df = df.style.apply(
                                color_row, axis=1
                            ).applymap(
                                color_eligible_cell,
                                subset=["Eligible"]
                            )

                            st.dataframe(styled_df, use_container_width=True, height=400)

                            # Download results
                            csv_buffer = io.StringIO()
                            df.to_csv(csv_buffer, index=False)
                            st.download_button(
                                label="Download Results CSV",
                                data=csv_buffer.getvalue(),
                                file_name="classification_results.csv",
                                mime="text/csv",
                            )

                        # Errors
                        if result.get("errors"):
                            st.markdown("---")
                            st.header("Errors")
                            for error in result["errors"]:
                                st.error(str(error))

                    else:
                        st.error(f"API Error: {response.status_code}")
                        st.json(response.json())

                except httpx.ConnectError:
                    st.error(
                        "Could not connect to the API. "
                        "Make sure the API server is running."
                    )
                except Exception as e:
                    st.error(f"Error: {str(e)}")
