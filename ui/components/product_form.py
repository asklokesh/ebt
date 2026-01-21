"""Product input form component."""

import streamlit as st
from typing import Dict, Any, Optional


def render_product_form() -> Optional[Dict[str, Any]]:
    """
    Render the product input form.

    Returns:
        Product data dict if form is submitted, None otherwise
    """
    st.subheader("Product Information")

    with st.form("product_form"):
        col1, col2 = st.columns(2)

        with col1:
            product_id = st.text_input(
                "Product ID *",
                placeholder="SKU-12345",
                help="Unique identifier (UPC, SKU, or internal ID)",
            )

            product_name = st.text_input(
                "Product Name *",
                placeholder="Monster Energy Drink Original",
                help="Human-readable product name",
            )

            category = st.selectbox(
                "Category",
                options=[
                    "",
                    "Beverages",
                    "Snacks",
                    "Produce",
                    "Dairy",
                    "Meat",
                    "Bakery",
                    "Frozen Foods",
                    "Canned Goods",
                    "Condiments",
                    "Baby Food",
                    "Health",
                    "Tobacco",
                    "Other",
                ],
                help="Product category",
            )

            brand = st.text_input(
                "Brand",
                placeholder="Monster",
                help="Brand name",
            )

        with col2:
            upc = st.text_input(
                "UPC Code",
                placeholder="070847811169",
                help="12-14 digit barcode",
            )

            nutrition_label_type = st.selectbox(
                "Nutrition Label Type",
                options=[
                    "",
                    "nutrition_facts",
                    "supplement_facts",
                    "none",
                ],
                format_func=lambda x: {
                    "": "Select...",
                    "nutrition_facts": "Nutrition Facts",
                    "supplement_facts": "Supplement Facts",
                    "none": "No Label",
                }.get(x, x),
                help="Type of nutrition label on the product",
            )

            description = st.text_area(
                "Description",
                placeholder="Energy drink with caffeine and B vitamins",
                height=100,
                help="Product description",
            )

        st.subheader("Product Attributes")

        col3, col4 = st.columns(2)

        with col3:
            is_hot_at_sale = st.checkbox(
                "Hot at Point of Sale",
                help="Is the product hot when sold?",
            )

            is_for_onsite_consumption = st.checkbox(
                "For On-Site Consumption",
                help="Intended to be consumed on premises?",
            )

            contains_tobacco = st.checkbox(
                "Contains Tobacco/Nicotine",
                help="Contains tobacco or nicotine products?",
            )

        with col4:
            contains_cbd_cannabis = st.checkbox(
                "Contains CBD/Cannabis",
                help="Contains CBD or cannabis?",
            )

            is_live_animal = st.checkbox(
                "Live Animal",
                help="Is this a live animal?",
            )

            alcohol_content = st.number_input(
                "Alcohol Content (%)",
                min_value=0.0,
                max_value=100.0,
                value=0.0,
                step=0.1,
                help="Alcohol by volume percentage",
            )

        ingredients = st.text_area(
            "Ingredients (comma-separated)",
            placeholder="carbonated water, sugar, glucose, citric acid, taurine, caffeine",
            help="List of ingredients separated by commas",
        )

        submitted = st.form_submit_button("Classify Product", type="primary")

        if submitted:
            if not product_id or not product_name:
                st.error("Product ID and Product Name are required.")
                return None

            # Parse ingredients
            ingredients_list = None
            if ingredients:
                ingredients_list = [i.strip() for i in ingredients.split(",") if i.strip()]

            return {
                "product_id": product_id,
                "product_name": product_name,
                "description": description if description else None,
                "category": category if category else None,
                "brand": brand if brand else None,
                "upc": upc if upc else None,
                "ingredients": ingredients_list,
                "nutrition_label_type": nutrition_label_type if nutrition_label_type else None,
                "is_hot_at_sale": is_hot_at_sale,
                "is_for_onsite_consumption": is_for_onsite_consumption,
                "alcohol_content": alcohol_content / 100 if alcohol_content > 0 else None,
                "contains_tobacco": contains_tobacco,
                "contains_cbd_cannabis": contains_cbd_cannabis,
                "is_live_animal": is_live_animal,
            }

    return None
