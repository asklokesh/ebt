"""Decision tree tool for rule-based classification decisions."""

from typing import Any, Dict, Optional

from src.utils.logging import get_logger

logger = get_logger(__name__)


class DecisionTreeTool:
    """Tool for applying SNAP eligibility decision tree."""

    name: str = "decision_tree"
    description: str = (
        "Apply the SNAP eligibility decision tree to determine product eligibility. "
        "Input should be a JSON string with product attributes."
    )

    # Decision tree rules
    RULES = [
        {
            "question": "Is it intended for human consumption?",
            "check": lambda p: p.get("is_human_food", True),
            "false_result": ("INELIGIBLE", "INELIGIBLE_NON_FOOD"),
        },
        {
            "question": "Does it contain alcohol (>0.5% ABV)?",
            "check": lambda p: (p.get("alcohol_content") or 0) <= 0.005,
            "false_result": ("INELIGIBLE", "INELIGIBLE_ALCOHOL"),
        },
        {
            "question": "Is it a tobacco or nicotine product?",
            "check": lambda p: not p.get("contains_tobacco", False),
            "false_result": ("INELIGIBLE", "INELIGIBLE_TOBACCO"),
        },
        {
            "question": "Does it have a Supplement Facts label?",
            "check": lambda p: p.get("nutrition_label_type") != "supplement_facts",
            "false_result": ("INELIGIBLE", "INELIGIBLE_SUPPLEMENT"),
        },
        {
            "question": "Is it hot at the point of sale?",
            "check": lambda p: not p.get("is_hot_at_sale", False),
            "false_result": ("INELIGIBLE", "INELIGIBLE_HOT_FOOD"),
        },
        {
            "question": "Is it intended for on-premises consumption?",
            "check": lambda p: not p.get("is_for_onsite_consumption", False),
            "false_result": ("INELIGIBLE", "INELIGIBLE_ONSITE_CONSUMPTION"),
        },
        {
            "question": "Does it contain cannabis/CBD/controlled substances?",
            "check": lambda p: not p.get("contains_cbd_cannabis", False),
            "false_result": ("INELIGIBLE", "INELIGIBLE_CBD_CANNABIS"),
        },
        {
            "question": "Is it a live animal (not shellfish/fish)?",
            "check": lambda p: not p.get("is_live_animal", False),
            "false_result": ("INELIGIBLE", "INELIGIBLE_LIVE_ANIMAL"),
        },
    ]

    def run(self, product_attributes: Dict[str, Any]) -> str:
        """
        Apply decision tree to product attributes.

        Args:
            product_attributes: Dict of product attributes

        Returns:
            Decision tree result as formatted string
        """
        logger.info("decision_tree_evaluation", product=product_attributes)

        reasoning = []

        for rule in self.RULES:
            question = rule["question"]
            passed = rule["check"](product_attributes)

            if passed:
                reasoning.append(f"PASS: {question} -> Continue")
            else:
                eligibility, category = rule["false_result"]
                reasoning.append(f"FAIL: {question} -> {eligibility}")

                return self._format_result(
                    eligibility="INELIGIBLE",
                    category=category,
                    reasoning=reasoning,
                )

        # All rules passed - eligible
        reasoning.append("All checks passed -> ELIGIBLE")

        return self._format_result(
            eligibility="ELIGIBLE",
            category="ELIGIBLE_OTHER",
            reasoning=reasoning,
        )

    async def arun(self, product_attributes: Dict[str, Any]) -> str:
        """Async execution - wraps sync version."""
        return self.run(product_attributes)

    def _format_result(
        self,
        eligibility: str,
        category: str,
        reasoning: list[str],
    ) -> str:
        """
        Format decision tree result.

        Args:
            eligibility: ELIGIBLE or INELIGIBLE
            category: Classification category
            reasoning: List of reasoning steps

        Returns:
            Formatted string
        """
        parts = [
            "Decision Tree Analysis:",
            f"Result: {eligibility}",
            f"Category: {category}",
            "",
            "Reasoning Steps:",
        ]

        for i, step in enumerate(reasoning, 1):
            parts.append(f"  {i}. {step}")

        return "\n".join(parts)

    def evaluate_single_rule(
        self,
        rule_name: str,
        value: Any,
    ) -> Optional[str]:
        """
        Evaluate a single rule.

        Args:
            rule_name: Name of the rule to evaluate
            value: Value to check

        Returns:
            Result if rule triggered, None otherwise
        """
        rule_map = {
            "alcohol": lambda v: v is not None and v > 0.005,
            "tobacco": lambda v: v is True,
            "hot_food": lambda v: v is True,
            "supplement": lambda v: v == "supplement_facts",
            "cbd_cannabis": lambda v: v is True,
            "live_animal": lambda v: v is True,
            "onsite_consumption": lambda v: v is True,
        }

        if rule_name in rule_map:
            if rule_map[rule_name](value):
                return f"INELIGIBLE_{rule_name.upper()}"

        return None
