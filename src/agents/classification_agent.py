"""
LangChain-based AI reasoning agent for EBT eligibility classification.
Uses Gemini API with RAG for SNAP regulation lookup.
"""

import re
from typing import Optional

from src.agents.prompts.classification_prompt import format_classification_prompt
from src.agents.prompts.system_prompt import get_system_prompt
from src.agents.tools.regulation_lookup import RegulationLookupTool
from src.core.config import settings
from src.core.constants import ClassificationCategory
from src.core.exceptions import AIReasoningError
from src.models.classification import AIReasoningResult, RuleValidationResult
from src.models.product import ProductInput
from src.models.regulation import RegulationCitation
from src.rag.retriever import SNAPRegulationRetriever, get_retriever
from src.utils.logging import get_logger

logger = get_logger(__name__)


class ClassificationAgent:
    """
    AI agent for classifying ambiguous products using Gemini + RAG.

    This agent is called when rule-based validation cannot make a
    deterministic decision and AI reasoning is required.
    """

    def __init__(
        self,
        retriever: SNAPRegulationRetriever = None,
        model_name: str = None,
    ):
        """
        Initialize the classification agent.

        Args:
            retriever: RAG retriever for regulations
            model_name: LLM model name
        """
        self.model_name = model_name or settings.gemini_model
        self.retriever = retriever or get_retriever()
        self.regulation_tool = RegulationLookupTool(self.retriever)
        self._llm = None

    @property
    def llm(self):
        """Lazy load the LLM."""
        if self._llm is None:
            if not settings.is_gemini_configured:
                logger.warning("gemini_not_configured")
                return None

            try:
                from langchain_google_genai import ChatGoogleGenerativeAI

                self._llm = ChatGoogleGenerativeAI(
                    model=self.model_name,
                    google_api_key=settings.google_api_key,
                    temperature=0.1,  # Low temperature for consistent classification
                )
                logger.info("llm_initialized", model=self.model_name)
            except Exception as e:
                logger.error("llm_initialization_failed", error=str(e))
                raise AIReasoningError(f"Failed to initialize LLM: {e}")

        return self._llm

    async def reason(
        self,
        product: ProductInput,
        partial_rule_result: Optional[RuleValidationResult] = None,
    ) -> AIReasoningResult:
        """
        Use AI reasoning to classify a product.

        Args:
            product: Product to classify
            partial_rule_result: Partial result from rule-based validation

        Returns:
            AIReasoningResult with classification details
        """
        logger.info(
            "ai_reasoning_started",
            product_id=product.product_id,
            product_name=product.product_name,
        )

        try:
            # Step 1: Retrieve relevant regulations
            retrieved_docs = self.retriever.retrieve_for_classification(
                product_name=product.product_name,
                category=product.category,
                description=product.description,
                k=3,
            )
            regulations_context = self.retriever.format_context(retrieved_docs)

            # Step 2: Format the partial rule analysis
            partial_analysis = self._format_partial_analysis(partial_rule_result)

            # Step 3: Build the prompt
            prompt = self._build_prompt(product, partial_analysis, regulations_context)

            # Step 4: Get LLM response
            if self.llm is None:
                # Fallback if LLM not configured
                logger.warning("llm_not_available_using_fallback")
                return self._fallback_classification(product)

            response = await self._invoke_llm(prompt)

            # Step 5: Parse the response
            result = self._parse_response(response, product)

            logger.info(
                "ai_reasoning_completed",
                product_id=product.product_id,
                is_eligible=result.is_eligible,
                category=result.category.value,
            )

            return result

        except Exception as e:
            logger.error(
                "ai_reasoning_failed",
                error=str(e),
                product_id=product.product_id,
            )
            # Return fallback classification
            return self._fallback_classification(product, str(e))

    def _format_partial_analysis(
        self,
        partial_rule_result: Optional[RuleValidationResult],
    ) -> str:
        """Format the partial rule analysis for the prompt."""
        if not partial_rule_result:
            return "No prior rule analysis available."

        parts = [
            "Previous Rule Analysis:",
            f"- Deterministic: {partial_rule_result.is_deterministic}",
            f"- Reasoning: {'; '.join(partial_rule_result.reasoning_chain)}",
            f"- Key factors: {', '.join(partial_rule_result.key_factors)}",
        ]

        if partial_rule_result.ambiguity_reason:
            parts.append(f"- Ambiguity reason: {partial_rule_result.ambiguity_reason}")

        return "\n".join(parts)

    def _build_prompt(
        self,
        product: ProductInput,
        partial_analysis: str,
        regulations_context: str,
    ) -> str:
        """Build the full prompt for the LLM."""
        return format_classification_prompt(
            product_id=product.product_id,
            product_name=product.product_name,
            description=product.description or "Not provided",
            category=product.category or "Unknown",
            brand=product.brand or "Unknown",
            upc=product.upc or "Not provided",
            ingredients=(
                ", ".join(product.ingredients)
                if product.ingredients
                else "Not provided"
            ),
            nutrition_label_type=product.nutrition_label_type or "Unknown",
            is_hot_at_sale=(
                str(product.is_hot_at_sale)
                if product.is_hot_at_sale is not None
                else "Unknown"
            ),
            is_for_onsite_consumption=(
                str(product.is_for_onsite_consumption)
                if product.is_for_onsite_consumption is not None
                else "Unknown"
            ),
            alcohol_content=(
                f"{product.alcohol_content * 100:.1f}%"
                if product.alcohol_content
                else "0%"
            ),
            contains_tobacco=(
                str(product.contains_tobacco)
                if product.contains_tobacco is not None
                else "Unknown"
            ),
            contains_cbd_cannabis=(
                str(product.contains_cbd_cannabis)
                if product.contains_cbd_cannabis is not None
                else "Unknown"
            ),
            is_live_animal=(
                str(product.is_live_animal)
                if product.is_live_animal is not None
                else "No"
            ),
            partial_rule_analysis=partial_analysis,
            retrieved_regulations=regulations_context,
        )

    async def _invoke_llm(self, prompt: str) -> str:
        """Invoke the LLM with the prompt."""
        system_prompt = get_system_prompt()

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt},
        ]

        # Use ainvoke for async
        response = await self.llm.ainvoke(messages)

        return response.content

    def _parse_response(
        self,
        response: str,
        product: ProductInput,
    ) -> AIReasoningResult:
        """Parse the LLM response into a structured result."""
        response_lower = response.lower()

        # Extract eligibility
        is_eligible = self._extract_eligibility(response_lower)

        # Extract category
        category = self._extract_category(response, response_lower, is_eligible)

        # Extract reasoning chain
        reasoning_chain = self._extract_reasoning(response)

        # Extract key factors
        key_factors = self._extract_key_factors(response, product)

        # Extract citations
        citations = self._extract_citations(response)

        return AIReasoningResult(
            is_eligible=is_eligible,
            category=category,
            reasoning_chain=reasoning_chain,
            citations=citations,
            key_factors=key_factors,
            data_sources_used=["Gemini AI", "SNAP Regulation Vector Store"],
        )

    def _extract_eligibility(self, response_lower: str) -> bool:
        """Extract eligibility determination from response."""
        # Look for explicit eligibility statement
        if "eligibility: eligible" in response_lower:
            return True
        elif "eligibility: ineligible" in response_lower:
            return False

        # Look for common phrases
        ineligible_phrases = [
            "not eligible",
            "ineligible",
            "cannot be purchased",
            "not allowed",
            "prohibited",
            "excluded from snap",
        ]

        eligible_phrases = [
            "is eligible",
            "eligible for snap",
            "can be purchased",
            "allowed under snap",
            "permitted",
        ]

        for phrase in ineligible_phrases:
            if phrase in response_lower:
                return False

        for phrase in eligible_phrases:
            if phrase in response_lower:
                return True

        # Default to eligible for food items
        return True

    def _extract_category(
        self,
        response: str,
        response_lower: str,
        is_eligible: bool,
    ) -> ClassificationCategory:
        """Extract classification category from response."""
        # Try to find explicit category
        category_match = re.search(
            r"category:\s*([A-Z_]+)",
            response,
            re.IGNORECASE,
        )

        if category_match:
            category_str = category_match.group(1).upper()
            try:
                return ClassificationCategory(category_str)
            except ValueError:
                pass

        # Infer from content
        if not is_eligible:
            if "alcohol" in response_lower:
                return ClassificationCategory.INELIGIBLE_ALCOHOL
            elif "tobacco" in response_lower:
                return ClassificationCategory.INELIGIBLE_TOBACCO
            elif "hot" in response_lower and "food" in response_lower:
                return ClassificationCategory.INELIGIBLE_HOT_FOOD
            elif "supplement" in response_lower:
                return ClassificationCategory.INELIGIBLE_SUPPLEMENT
            elif "medicine" in response_lower or "vitamin" in response_lower:
                return ClassificationCategory.INELIGIBLE_MEDICINE
            elif "cbd" in response_lower or "cannabis" in response_lower:
                return ClassificationCategory.INELIGIBLE_CBD_CANNABIS
            elif "live animal" in response_lower:
                return ClassificationCategory.INELIGIBLE_LIVE_ANIMAL
            elif "non-food" in response_lower or "non food" in response_lower:
                return ClassificationCategory.INELIGIBLE_NON_FOOD
            else:
                return ClassificationCategory.INELIGIBLE_OTHER
        else:
            if "staple" in response_lower:
                return ClassificationCategory.ELIGIBLE_STAPLE_FOOD
            elif "snack" in response_lower:
                return ClassificationCategory.ELIGIBLE_SNACK_FOOD
            elif "beverage" in response_lower or "drink" in response_lower:
                return ClassificationCategory.ELIGIBLE_BEVERAGE
            elif "baby" in response_lower or "infant" in response_lower:
                return ClassificationCategory.ELIGIBLE_BABY_FOOD
            elif "seed" in response_lower or "plant" in response_lower:
                return ClassificationCategory.ELIGIBLE_SEEDS_PLANTS
            elif "cooking" in response_lower or "ingredient" in response_lower:
                return ClassificationCategory.ELIGIBLE_COOKING_INGREDIENT
            else:
                return ClassificationCategory.ELIGIBLE_OTHER

    def _extract_reasoning(self, response: str) -> list[str]:
        """Extract reasoning chain from response."""
        reasoning = []

        # Look for numbered reasoning steps
        numbered_pattern = r"^\s*(\d+)\.\s*(.+)$"
        lines = response.split("\n")

        in_reasoning_section = False
        for line in lines:
            if "reasoning" in line.lower() and ":" in line:
                in_reasoning_section = True
                continue

            if in_reasoning_section:
                # Check for section end
                if line.strip() and not line.strip()[0].isdigit() and ":" in line:
                    in_reasoning_section = False
                    continue

                match = re.match(numbered_pattern, line)
                if match:
                    reasoning.append(match.group(2).strip())
                elif line.strip().startswith("-"):
                    reasoning.append(line.strip()[1:].strip())

        # If no structured reasoning found, extract key sentences
        if not reasoning:
            sentences = re.split(r"[.!?]+", response)
            for sentence in sentences[:5]:
                sentence = sentence.strip()
                if len(sentence) > 20 and any(
                    kw in sentence.lower()
                    for kw in ["eligible", "ineligible", "snap", "because", "therefore"]
                ):
                    reasoning.append(sentence)

        return reasoning[:10]  # Limit to 10 steps

    def _extract_key_factors(
        self,
        response: str,
        product: ProductInput,
    ) -> list[str]:
        """Extract key factors from response."""
        factors = []

        # Look for key_factors section
        if "key_factors" in response.lower() or "key factors" in response.lower():
            in_factors = False
            for line in response.split("\n"):
                if "key_factors" in line.lower() or "key factors" in line.lower():
                    in_factors = True
                    continue

                if in_factors:
                    if line.strip().startswith("-"):
                        factors.append(line.strip()[1:].strip())
                    elif line.strip() and ":" in line:
                        in_factors = False

        # Add product-based factors
        if product.nutrition_label_type:
            if product.nutrition_label_type == "nutrition_facts":
                factors.append("Has Nutrition Facts label")
            elif product.nutrition_label_type == "supplement_facts":
                factors.append("Has Supplement Facts label")

        if product.category:
            factors.append(f"Category: {product.category}")

        return list(set(factors))[:5]

    def _extract_citations(self, response: str) -> list[RegulationCitation]:
        """Extract regulation citations from response."""
        citations = []

        # Look for common regulation patterns
        cfr_pattern = r"7\s*CFR\s*(?:section\s*)?(?:§\s*)?271\.2"
        fns_pattern = r"FNS\s+(?:Policy|guidance|rule)"

        if re.search(cfr_pattern, response, re.IGNORECASE):
            citations.append(
                RegulationCitation(
                    regulation_id="7 CFR 271.2",
                    section="eligible food",
                    excerpt="Referenced in AI analysis",
                    relevance_score=0.9,
                    source_url="https://www.ecfr.gov/current/title-7/section-271.2",
                )
            )

        if re.search(fns_pattern, response, re.IGNORECASE):
            citations.append(
                RegulationCitation(
                    regulation_id="FNS Policy",
                    section="eligible food items",
                    excerpt="Referenced in AI analysis",
                    relevance_score=0.85,
                    source_url="https://www.fns.usda.gov/snap/eligible-food-items",
                )
            )

        return citations

    def _fallback_classification(
        self,
        product: ProductInput,
        error_msg: str = None,
    ) -> AIReasoningResult:
        """
        Provide a fallback classification when AI is unavailable.

        Args:
            product: Product to classify
            error_msg: Error message if applicable

        Returns:
            Conservative fallback classification
        """
        reasoning = [
            "AI reasoning was not available or encountered an error",
        ]

        if error_msg:
            reasoning.append(f"Error: {error_msg}")

        reasoning.append(
            "Applying conservative classification based on available attributes"
        )

        # Conservative approach: assume eligible unless clearly ineligible
        is_eligible = True
        category = ClassificationCategory.ELIGIBLE_OTHER

        # Check for clear ineligibility
        if product.nutrition_label_type == "supplement_facts":
            is_eligible = False
            category = ClassificationCategory.INELIGIBLE_SUPPLEMENT
            reasoning.append("Product has Supplement Facts label - ineligible")

        return AIReasoningResult(
            is_eligible=is_eligible,
            category=category,
            reasoning_chain=reasoning,
            citations=[],
            key_factors=["Manual review recommended"],
            data_sources_used=["Fallback logic"],
        )
