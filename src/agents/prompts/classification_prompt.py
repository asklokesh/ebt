"""Classification prompt template for the EBT classification agent."""

CLASSIFICATION_PROMPT_TEMPLATE = """Classify this product for SNAP/EBT eligibility:

## Product Information
- Product ID: {product_id}
- Name: {product_name}
- Description: {description}
- Category: {category}
- Brand: {brand}
- UPC: {upc}
- Ingredients: {ingredients}
- Label Type: {nutrition_label_type}
- Hot at Sale: {is_hot_at_sale}
- For On-site Consumption: {is_for_onsite_consumption}
- Alcohol Content: {alcohol_content}
- Contains Tobacco: {contains_tobacco}
- Contains CBD/Cannabis: {contains_cbd_cannabis}
- Is Live Animal: {is_live_animal}

## Partial Rule Analysis
{partial_rule_analysis}

## Retrieved Regulations
{retrieved_regulations}

## Instructions
1. Analyze all product attributes against SNAP rules
2. Consider the retrieved regulations
3. Provide step-by-step reasoning
4. Cite specific regulations
5. Return final classification in the specified format

Think step by step and be thorough in your analysis."""


def format_classification_prompt(
    product_id: str,
    product_name: str,
    description: str = "Not provided",
    category: str = "Unknown",
    brand: str = "Unknown",
    upc: str = "Not provided",
    ingredients: str = "Not provided",
    nutrition_label_type: str = "Unknown",
    is_hot_at_sale: str = "Unknown",
    is_for_onsite_consumption: str = "Unknown",
    alcohol_content: str = "0%",
    contains_tobacco: str = "Unknown",
    contains_cbd_cannabis: str = "Unknown",
    is_live_animal: str = "No",
    partial_rule_analysis: str = "",
    retrieved_regulations: str = "No regulations retrieved.",
) -> str:
    """
    Format the classification prompt with product data.

    Args:
        product_id: Product identifier
        product_name: Product name
        description: Product description
        category: Product category
        brand: Brand name
        upc: UPC code
        ingredients: Comma-separated ingredients
        nutrition_label_type: Type of nutrition label
        is_hot_at_sale: Whether hot at sale
        is_for_onsite_consumption: Whether for onsite consumption
        alcohol_content: Alcohol content percentage
        contains_tobacco: Whether contains tobacco
        contains_cbd_cannabis: Whether contains CBD/cannabis
        is_live_animal: Whether live animal
        partial_rule_analysis: Results from rule-based validation
        retrieved_regulations: Retrieved regulation text

    Returns:
        Formatted prompt string
    """
    return CLASSIFICATION_PROMPT_TEMPLATE.format(
        product_id=product_id,
        product_name=product_name,
        description=description,
        category=category,
        brand=brand,
        upc=upc,
        ingredients=ingredients,
        nutrition_label_type=nutrition_label_type,
        is_hot_at_sale=is_hot_at_sale,
        is_for_onsite_consumption=is_for_onsite_consumption,
        alcohol_content=alcohol_content,
        contains_tobacco=contains_tobacco,
        contains_cbd_cannabis=contains_cbd_cannabis,
        is_live_animal=is_live_animal,
        partial_rule_analysis=partial_rule_analysis,
        retrieved_regulations=retrieved_regulations,
    )
