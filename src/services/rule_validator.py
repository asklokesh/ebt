"""
Rule-based validator implementing SNAP eligibility rules from 7 CFR 271.2.
Handles clear-cut cases without requiring AI reasoning.
"""

from typing import Optional

from src.core.constants import (
    ALCOHOL_THRESHOLD,
    CLEARLY_ELIGIBLE_CATEGORIES,
    ClassificationCategory,
)
from src.models.classification import RuleValidationResult
from src.models.product import ProductInput
from src.models.regulation import RegulationCitation
from src.utils.logging import get_logger

logger = get_logger(__name__)


class RuleValidator:
    """
    Implements deterministic SNAP eligibility rules.

    These rules cover clear-cut cases that don't require AI reasoning:
    - Alcohol (always ineligible)
    - Tobacco (always ineligible)
    - Hot foods (always ineligible)
    - On-site consumption (always ineligible)
    - Supplements with Supplement Facts label (always ineligible)
    - Live animals except exceptions (always ineligible)
    - CBD/Cannabis products (always ineligible)
    """

    # Regulation citations for each rule
    CITATIONS = {
        "alcohol": RegulationCitation(
            regulation_id="7 CFR 271.2",
            section="eligible food",
            excerpt="Eligible food means any food or food product for home consumption except alcoholic beverages",
            relevance_score=1.0,
            source_url="https://www.ecfr.gov/current/title-7/section-271.2",
        ),
        "tobacco": RegulationCitation(
            regulation_id="7 CFR 271.2",
            section="eligible food",
            excerpt="Eligible food means any food or food product for home consumption except tobacco",
            relevance_score=1.0,
            source_url="https://www.ecfr.gov/current/title-7/section-271.2",
        ),
        "hot_food": RegulationCitation(
            regulation_id="7 CFR 271.2",
            section="eligible food",
            excerpt="Hot foods or hot food products ready for immediate consumption are not eligible",
            relevance_score=1.0,
            source_url="https://www.ecfr.gov/current/title-7/section-271.2",
        ),
        "onsite_consumption": RegulationCitation(
            regulation_id="7 CFR 271.2",
            section="eligible food",
            excerpt="Foods prepared for on-premises consumption are not eligible for SNAP purchase",
            relevance_score=1.0,
            source_url="https://www.ecfr.gov/current/title-7/section-271.2",
        ),
        "supplement": RegulationCitation(
            regulation_id="FNS Policy",
            section="eligible food items",
            excerpt="Any item that has a Supplement Facts label is considered a supplement and is not eligible for SNAP purchase",
            relevance_score=1.0,
            source_url="https://www.fns.usda.gov/snap/eligible-food-items",
        ),
        "cbd_cannabis": RegulationCitation(
            regulation_id="FNS Policy",
            section="eligible food items",
            excerpt="Food containing cannabis-derived products, such as CBD, and any other controlled substances, are not eligible to be purchased with SNAP benefits",
            relevance_score=1.0,
            source_url="https://www.fns.usda.gov/snap/food-determinations-eligible-foods",
        ),
        "live_animal": RegulationCitation(
            regulation_id="FNS Policy",
            section="eligible food items",
            excerpt="Live animals (except shellfish, fish removed from water, and animals slaughtered prior to pick-up from the store) are not eligible",
            relevance_score=1.0,
            source_url="https://www.fns.usda.gov/snap/eligible-food-items",
        ),
        "eligible_food": RegulationCitation(
            regulation_id="7 CFR 271.2",
            section="eligible food",
            excerpt="Any food or food product for home consumption",
            relevance_score=0.9,
            source_url="https://www.ecfr.gov/current/title-7/section-271.2",
        ),
        "seeds_plants": RegulationCitation(
            regulation_id="7 CFR 271.2",
            section="eligible food",
            excerpt="Seeds and plants for use in gardens to produce food for personal consumption",
            relevance_score=1.0,
            source_url="https://www.ecfr.gov/current/title-7/section-271.2",
        ),
    }

    def validate(self, product: ProductInput) -> RuleValidationResult:
        """
        Apply rule-based validation to determine eligibility.

        Returns deterministic result if rules apply, otherwise
        returns ambiguous result for AI processing.

        Args:
            product: Product input to validate

        Returns:
            RuleValidationResult with determination or ambiguity flag
        """
        reasoning = []
        key_factors = []

        logger.info(
            "rule_validation_started",
            product_id=product.product_id,
            product_name=product.product_name,
        )

        # Rule 1: Check for alcohol
        if product.alcohol_content is not None and product.alcohol_content > ALCOHOL_THRESHOLD:
            reasoning.append(
                f"Product contains {product.alcohol_content * 100:.1f}% alcohol"
            )
            reasoning.append(
                "Alcoholic beverages are explicitly excluded from SNAP eligibility"
            )
            return RuleValidationResult(
                is_deterministic=True,
                is_eligible=False,
                category=ClassificationCategory.INELIGIBLE_ALCOHOL,
                reasoning_chain=reasoning,
                citations=[self.CITATIONS["alcohol"]],
                key_factors=["Contains alcohol above 0.5% ABV"],
            )

        # Rule 2: Check for tobacco
        if product.contains_tobacco is True:
            reasoning.append("Product contains tobacco or nicotine")
            reasoning.append(
                "Tobacco products are explicitly excluded from SNAP eligibility"
            )
            return RuleValidationResult(
                is_deterministic=True,
                is_eligible=False,
                category=ClassificationCategory.INELIGIBLE_TOBACCO,
                reasoning_chain=reasoning,
                citations=[self.CITATIONS["tobacco"]],
                key_factors=["Contains tobacco/nicotine"],
            )

        # Rule 3: Check for hot food
        if product.is_hot_at_sale is True:
            reasoning.append("Product is hot at point of sale")
            reasoning.append(
                "Hot foods ready for immediate consumption are not eligible"
            )
            return RuleValidationResult(
                is_deterministic=True,
                is_eligible=False,
                category=ClassificationCategory.INELIGIBLE_HOT_FOOD,
                reasoning_chain=reasoning,
                citations=[self.CITATIONS["hot_food"]],
                key_factors=["Hot at point of sale"],
            )

        # Rule 4: Check for on-premises consumption
        if product.is_for_onsite_consumption is True:
            reasoning.append("Product is intended for on-premises consumption")
            reasoning.append(
                "Foods for on-premises consumption are not eligible"
            )
            return RuleValidationResult(
                is_deterministic=True,
                is_eligible=False,
                category=ClassificationCategory.INELIGIBLE_ONSITE_CONSUMPTION,
                reasoning_chain=reasoning,
                citations=[self.CITATIONS["onsite_consumption"]],
                key_factors=["Intended for on-premises consumption"],
            )

        # Rule 5: Check for Supplement Facts label
        if product.nutrition_label_type == "supplement_facts":
            reasoning.append(
                "Product has a Supplement Facts label (not Nutrition Facts)"
            )
            reasoning.append(
                "Items with Supplement Facts labels are classified as supplements, not food"
            )
            return RuleValidationResult(
                is_deterministic=True,
                is_eligible=False,
                category=ClassificationCategory.INELIGIBLE_SUPPLEMENT,
                reasoning_chain=reasoning,
                citations=[self.CITATIONS["supplement"]],
                key_factors=["Has Supplement Facts label"],
            )

        # Rule 6: Check for CBD/Cannabis
        if product.contains_cbd_cannabis is True:
            reasoning.append(
                "Product contains CBD, cannabis, or controlled substances"
            )
            reasoning.append(
                "Products with cannabis-derived ingredients are not eligible"
            )
            return RuleValidationResult(
                is_deterministic=True,
                is_eligible=False,
                category=ClassificationCategory.INELIGIBLE_CBD_CANNABIS,
                reasoning_chain=reasoning,
                citations=[self.CITATIONS["cbd_cannabis"]],
                key_factors=["Contains CBD/cannabis"],
            )

        # Rule 7: Check for live animals
        if product.is_live_animal is True:
            reasoning.append("Product is a live animal")
            reasoning.append(
                "Live animals are not eligible (except shellfish, fish removed from water, animals slaughtered before pickup)"
            )
            return RuleValidationResult(
                is_deterministic=True,
                is_eligible=False,
                category=ClassificationCategory.INELIGIBLE_LIVE_ANIMAL,
                reasoning_chain=reasoning,
                citations=[self.CITATIONS["live_animal"]],
                key_factors=["Live animal"],
            )

        # No disqualifying rules triggered - check if we can positively classify
        # If product has Nutrition Facts label and category suggests food, likely eligible
        if product.nutrition_label_type == "nutrition_facts":
            key_factors.append("Has Nutrition Facts label")

            # Check if category is a known eligible category
            if product.category:
                category_lower = product.category.lower()
                if any(cat in category_lower for cat in CLEARLY_ELIGIBLE_CATEGORIES):
                    reasoning.append(
                        f"Product category '{product.category}' is a standard food category"
                    )
                    reasoning.append(
                        "Product has Nutrition Facts label (not Supplement Facts)"
                    )
                    reasoning.append(
                        "No disqualifying factors found (alcohol, tobacco, hot, etc.)"
                    )
                    reasoning.append(
                        "Product is eligible as a standard food item for home consumption"
                    )

                    # Determine more specific category
                    category = self._determine_eligible_category(product)

                    return RuleValidationResult(
                        is_deterministic=True,
                        is_eligible=True,
                        category=category,
                        reasoning_chain=reasoning,
                        citations=[self.CITATIONS["eligible_food"]],
                        key_factors=key_factors + [f"Category: {product.category}"],
                    )

        # Check for seeds/plants
        if product.category:
            category_lower = product.category.lower()
            if "seed" in category_lower or "plant" in category_lower:
                reasoning.append(
                    f"Product is in category '{product.category}'"
                )
                reasoning.append(
                    "Seeds and plants that produce food are eligible"
                )
                return RuleValidationResult(
                    is_deterministic=True,
                    is_eligible=True,
                    category=ClassificationCategory.ELIGIBLE_SEEDS_PLANTS,
                    reasoning_chain=reasoning,
                    citations=[self.CITATIONS["seeds_plants"]],
                    key_factors=["Seeds/plants for food production"],
                )

        # Ambiguous case - needs AI reasoning
        reasoning.append(
            "Initial rule-based validation passed (no disqualifying factors)"
        )
        reasoning.append("Product requires AI reasoning for final classification")

        logger.info(
            "rule_validation_ambiguous",
            product_id=product.product_id,
            key_factors=key_factors,
        )

        return RuleValidationResult(
            is_deterministic=False,
            is_eligible=None,
            category=None,
            reasoning_chain=reasoning,
            citations=[],
            key_factors=key_factors,
            ambiguity_reason="Product does not match clear-cut rules; AI reasoning required",
        )

    def _determine_eligible_category(
        self, product: ProductInput
    ) -> ClassificationCategory:
        """
        Determine the specific eligible category based on product attributes.

        Args:
            product: Product input

        Returns:
            Appropriate ClassificationCategory
        """
        category_lower = (product.category or "").lower()

        if any(c in category_lower for c in ["meat", "poultry", "fish", "seafood"]):
            return ClassificationCategory.ELIGIBLE_STAPLE_FOOD
        elif any(c in category_lower for c in ["produce", "fruit", "vegetable"]):
            return ClassificationCategory.ELIGIBLE_STAPLE_FOOD
        elif any(c in category_lower for c in ["dairy", "milk", "cheese", "yogurt"]):
            return ClassificationCategory.ELIGIBLE_STAPLE_FOOD
        elif any(
            c in category_lower for c in ["bread", "bakery", "cereal", "grain", "pasta"]
        ):
            return ClassificationCategory.ELIGIBLE_STAPLE_FOOD
        elif any(c in category_lower for c in ["beverage", "drink", "juice", "soda"]):
            return ClassificationCategory.ELIGIBLE_BEVERAGE
        elif any(c in category_lower for c in ["snack", "chip", "candy", "cookie"]):
            return ClassificationCategory.ELIGIBLE_SNACK_FOOD
        elif any(c in category_lower for c in ["baby", "infant", "formula"]):
            return ClassificationCategory.ELIGIBLE_BABY_FOOD
        elif any(c in category_lower for c in ["spice", "condiment", "sauce", "oil"]):
            return ClassificationCategory.ELIGIBLE_COOKING_INGREDIENT
        elif any(c in category_lower for c in ["seed", "plant"]):
            return ClassificationCategory.ELIGIBLE_SEEDS_PLANTS
        elif any(
            c in category_lower for c in ["frozen", "canned", "prepared", "ready"]
        ):
            return ClassificationCategory.ELIGIBLE_STAPLE_FOOD
        else:
            return ClassificationCategory.ELIGIBLE_OTHER
