"""Constants and enums for the EBT classification system."""

from enum import Enum


class ClassificationCategory(str, Enum):
    """Classification categories for EBT eligibility."""

    # Eligible categories
    ELIGIBLE_STAPLE_FOOD = "ELIGIBLE_STAPLE_FOOD"
    ELIGIBLE_SNACK_FOOD = "ELIGIBLE_SNACK_FOOD"
    ELIGIBLE_BEVERAGE = "ELIGIBLE_BEVERAGE"
    ELIGIBLE_COOKING_INGREDIENT = "ELIGIBLE_COOKING_INGREDIENT"
    ELIGIBLE_BABY_FOOD = "ELIGIBLE_BABY_FOOD"
    ELIGIBLE_SEEDS_PLANTS = "ELIGIBLE_SEEDS_PLANTS"
    ELIGIBLE_OTHER = "ELIGIBLE_OTHER"

    # Ineligible categories
    INELIGIBLE_ALCOHOL = "INELIGIBLE_ALCOHOL"
    INELIGIBLE_TOBACCO = "INELIGIBLE_TOBACCO"
    INELIGIBLE_HOT_FOOD = "INELIGIBLE_HOT_FOOD"
    INELIGIBLE_ONSITE_CONSUMPTION = "INELIGIBLE_ONSITE_CONSUMPTION"
    INELIGIBLE_SUPPLEMENT = "INELIGIBLE_SUPPLEMENT"
    INELIGIBLE_MEDICINE = "INELIGIBLE_MEDICINE"
    INELIGIBLE_NON_FOOD = "INELIGIBLE_NON_FOOD"
    INELIGIBLE_LIVE_ANIMAL = "INELIGIBLE_LIVE_ANIMAL"
    INELIGIBLE_CBD_CANNABIS = "INELIGIBLE_CBD_CANNABIS"
    INELIGIBLE_OTHER = "INELIGIBLE_OTHER"

    def is_eligible(self) -> bool:
        """Check if this category represents an eligible classification."""
        return self.value.startswith("ELIGIBLE_")


class NutritionLabelType(str, Enum):
    """Types of nutrition labels."""

    NUTRITION_FACTS = "nutrition_facts"
    SUPPLEMENT_FACTS = "supplement_facts"
    NONE = "none"


class RequestSource(str, Enum):
    """Sources of classification requests."""

    API = "API"
    UI = "UI"
    BATCH = "Batch"


# Alcohol content threshold (0.5% ABV)
ALCOHOL_THRESHOLD = 0.005

# Confidence score thresholds
CONFIDENCE_HIGH = 0.9
CONFIDENCE_MEDIUM = 0.7
CONFIDENCE_LOW = 0.5

# Clearly eligible food categories for rule-based classification
CLEARLY_ELIGIBLE_CATEGORIES = [
    "produce",
    "fruits",
    "vegetables",
    "meat",
    "poultry",
    "fish",
    "seafood",
    "dairy",
    "milk",
    "cheese",
    "yogurt",
    "bread",
    "bakery",
    "cereals",
    "grains",
    "pasta",
    "canned goods",
    "frozen foods",
    "snacks",
    "beverages",
    "condiments",
    "spices",
    "baby food",
    "infant formula",
]

# Model version
MODEL_VERSION = "1.0.0"
