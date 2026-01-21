"""Challenge workflow page."""

import streamlit as st
import httpx
import os

from ui.components.reasoning_chain import render_comparison

# API URL from environment or default
API_URL = os.environ.get("API_URL", "http://localhost:8000")


def render_challenge_page() -> None:
    """Render the challenge workflow page."""
    st.title("Challenge Classification")
    st.markdown(
        "Dispute a classification decision and provide additional evidence for re-evaluation."
    )

    # Audit ID lookup
    st.subheader("Step 1: Find Classification")

    audit_id = st.text_input(
        "Audit ID",
        placeholder="Enter the audit ID of the classification to challenge",
        help="You can find the audit ID in the classification result or audit trail",
    )

    # Use last classification if available
    if st.session_state.get("last_classification"):
        last_audit_id = st.session_state["last_classification"].get("audit_id")
        if st.button(f"Use Last Classification ({last_audit_id[:8]}...)"):
            audit_id = last_audit_id
            st.session_state["challenge_audit_id"] = audit_id
            st.rerun()

    if audit_id:
        # Fetch original classification
        with st.spinner("Loading original classification..."):
            try:
                response = httpx.get(
                    f"{API_URL}/explain/{audit_id}",
                    timeout=30.0,
                )

                if response.status_code == 200:
                    original = response.json()
                    st.session_state["original_classification"] = original

                    # Display original classification
                    st.markdown("---")
                    st.subheader("Original Classification")

                    col1, col2 = st.columns(2)

                    with col1:
                        classification = original.get("classification", {})
                        is_eligible = classification.get("is_ebt_eligible", False)

                        if is_eligible:
                            st.success("ELIGIBLE")
                        else:
                            st.error("INELIGIBLE")

                        st.write(f"**Category:** {classification.get('classification_category')}")
                        st.write(f"**Confidence:** {classification.get('confidence_score', 0) * 100:.0f}%")

                    with col2:
                        product = original.get("product", {})
                        st.write(f"**Product:** {product.get('product_name')}")
                        st.write(f"**ID:** {product.get('product_id')}")

                    # Reasoning
                    with st.expander("Original Reasoning"):
                        explanation = original.get("explanation", {})
                        for i, step in enumerate(explanation.get("reasoning_chain", []), 1):
                            st.write(f"{i}. {step}")

                elif response.status_code == 404:
                    st.error(f"Classification not found: {audit_id}")
                    st.session_state["original_classification"] = None
                else:
                    st.error(f"API Error: {response.status_code}")
                    st.session_state["original_classification"] = None

            except httpx.ConnectError:
                st.error("Could not connect to the API.")
            except Exception as e:
                st.error(f"Error: {str(e)}")

    # Challenge form
    if st.session_state.get("original_classification"):
        st.markdown("---")
        st.subheader("Step 2: Submit Challenge")

        with st.form("challenge_form"):
            challenge_reason = st.text_area(
                "Challenge Reason *",
                placeholder="Explain why you believe this classification is incorrect...",
                height=100,
                help="Provide a detailed reason for challenging this classification (min 10 characters)",
            )

            st.markdown("**Additional Evidence (Optional)**")
            st.caption("Provide updated information about the product")

            col_a, col_b = st.columns(2)

            with col_a:
                new_label_type = st.selectbox(
                    "Updated Label Type",
                    options=["", "nutrition_facts", "supplement_facts", "none"],
                    format_func=lambda x: {
                        "": "No change",
                        "nutrition_facts": "Nutrition Facts",
                        "supplement_facts": "Supplement Facts",
                        "none": "No Label",
                    }.get(x, x),
                )

                new_is_hot = st.selectbox(
                    "Updated Hot at Sale",
                    options=["", "true", "false"],
                    format_func=lambda x: {
                        "": "No change",
                        "true": "Yes",
                        "false": "No",
                    }.get(x, x),
                )

            with col_b:
                new_alcohol = st.number_input(
                    "Updated Alcohol Content (%)",
                    min_value=-1.0,
                    max_value=100.0,
                    value=-1.0,
                    step=0.1,
                    help="Set to -1 to keep original value",
                )

                new_tobacco = st.selectbox(
                    "Updated Contains Tobacco",
                    options=["", "true", "false"],
                    format_func=lambda x: {
                        "": "No change",
                        "true": "Yes",
                        "false": "No",
                    }.get(x, x),
                )

            new_description = st.text_area(
                "Updated Description",
                placeholder="Enter updated product description if applicable...",
            )

            submitted = st.form_submit_button("Submit Challenge", type="primary")

            if submitted:
                if not challenge_reason or len(challenge_reason) < 10:
                    st.error("Please provide a challenge reason (minimum 10 characters).")
                else:
                    # Build additional evidence
                    additional_evidence = {}

                    if new_label_type:
                        additional_evidence["new_nutrition_label_type"] = new_label_type

                    if new_is_hot:
                        additional_evidence["is_hot_at_sale"] = new_is_hot == "true"

                    if new_alcohol >= 0:
                        additional_evidence["alcohol_content"] = new_alcohol / 100

                    if new_tobacco:
                        additional_evidence["contains_tobacco"] = new_tobacco == "true"

                    if new_description:
                        additional_evidence["new_description"] = new_description

                    # Submit challenge
                    with st.spinner("Processing challenge..."):
                        try:
                            challenge_response = httpx.post(
                                f"{API_URL}/challenge/{audit_id}",
                                json={
                                    "challenge_reason": challenge_reason,
                                    "additional_evidence": additional_evidence if additional_evidence else None,
                                },
                                timeout=60.0,
                            )

                            if challenge_response.status_code == 200:
                                result = challenge_response.json()

                                st.success("Challenge processed successfully!")

                                st.markdown("---")
                                st.subheader("Challenge Result")

                                # Show comparison
                                original_class = result.get("original_classification", {})
                                new_class = result.get("new_classification", {})

                                render_comparison(original_class, new_class)

                                # Reasoning for change
                                st.markdown("---")
                                st.subheader("Reasoning")
                                for reason in result.get("reasoning_for_change", []):
                                    st.write(f"- {reason}")

                                # Store for future reference
                                st.session_state["last_challenge"] = result

                            else:
                                st.error(f"Challenge failed: {challenge_response.status_code}")
                                st.json(challenge_response.json())

                        except httpx.ConnectError:
                            st.error("Could not connect to the API.")
                        except Exception as e:
                            st.error(f"Error: {str(e)}")
