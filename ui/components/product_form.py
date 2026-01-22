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

    # Check if test product was set and apply to widget keys
    test_product = st.session_state.get("test_product", {})
    if test_product:
        # Set form field values in session state using widget keys
        st.session_state["form_product_id"] = test_product.get("product_id", "")
        st.session_state["form_product_name"] = test_product.get("product_name", "")
        st.session_state["form_brand"] = test_product.get("brand", "")
        st.session_state["form_upc"] = test_product.get("upc", "")
        st.session_state["form_description"] = test_product.get("description", "")
        st.session_state["form_is_hot_at_sale"] = test_product.get("is_hot_at_sale", False)
        st.session_state["form_is_for_onsite_consumption"] = test_product.get("is_for_onsite_consumption", False)
        st.session_state["form_contains_tobacco"] = test_product.get("contains_tobacco", False)
        st.session_state["form_contains_cbd_cannabis"] = test_product.get("contains_cbd_cannabis", False)
        st.session_state["form_is_live_animal"] = test_product.get("is_live_animal", False)

        # Handle alcohol content (stored as decimal in test_product)
        alcohol = test_product.get("alcohol_content", 0)
        if alcohol and alcohol < 1:
            alcohol = alcohol * 100  # Convert from decimal to percentage
        st.session_state["form_alcohol_content"] = float(alcohol) if alcohol else 0.0

        # Handle category index
        categories = [
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
        ]
        default_category = test_product.get("category", "")
        st.session_state["form_category"] = default_category if default_category in categories else ""

        # Handle nutrition label type
        label_types = ["", "nutrition_facts", "supplement_facts", "none"]
        default_label = test_product.get("nutrition_label_type", "")
        st.session_state["form_nutrition_label_type"] = default_label if default_label in label_types else ""

        # Clear test product after applying
        st.session_state["test_product"] = {}

    # Define category and label type options
    categories = [
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
    ]
    label_types = ["", "nutrition_facts", "supplement_facts", "none"]

    with st.form("product_form"):
        col1, col2 = st.columns(2)

        with col1:
            product_id = st.text_input(
                "Product ID *",
                key="form_product_id",
                placeholder="SKU-12345",
                help="Unique identifier (UPC, SKU, or internal ID)",
            )

            product_name = st.text_input(
                "Product Name *",
                key="form_product_name",
                placeholder="Monster Energy Drink Original",
                help="Human-readable product name",
            )

            category = st.selectbox(
                "Category",
                options=categories,
                key="form_category",
                help="Product category",
            )

            brand = st.text_input(
                "Brand",
                key="form_brand",
                placeholder="Monster",
                help="Brand name",
            )

        with col2:
            upc = st.text_input(
                "UPC Code",
                key="form_upc",
                placeholder="070847811169",
                help="12-14 digit barcode",
            )

            nutrition_label_type = st.selectbox(
                "Nutrition Label Type",
                options=label_types,
                key="form_nutrition_label_type",
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
                key="form_description",
                placeholder="Energy drink with caffeine and B vitamins",
                height=100,
                help="Product description",
            )

        st.subheader("Product Attributes")

        col3, col4 = st.columns(2)

        with col3:
            is_hot_at_sale = st.checkbox(
                "Hot at Point of Sale",
                key="form_is_hot_at_sale",
                help="Is the product hot when sold?",
            )

            is_for_onsite_consumption = st.checkbox(
                "For On-Site Consumption",
                key="form_is_for_onsite_consumption",
                help="Intended to be consumed on premises?",
            )

            contains_tobacco = st.checkbox(
                "Contains Tobacco/Nicotine",
                key="form_contains_tobacco",
                help="Contains tobacco or nicotine products?",
            )

        with col4:
            contains_cbd_cannabis = st.checkbox(
                "Contains CBD/Cannabis",
                key="form_contains_cbd_cannabis",
                help="Contains CBD or cannabis?",
            )

            is_live_animal = st.checkbox(
                "Live Animal",
                key="form_is_live_animal",
                help="Is this a live animal?",
            )

            alcohol_content = st.number_input(
                "Alcohol Content (%)",
                min_value=0.0,
                max_value=100.0,
                key="form_alcohol_content",
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
