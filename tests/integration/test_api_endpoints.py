"""Integration tests for API endpoints."""

import pytest
import pytest_asyncio
from httpx import AsyncClient


class TestClassifyEndpoint:
    """Test suite for /classify endpoint."""

    @pytest.mark.asyncio
    async def test_classify_eligible_product(self, async_client: AsyncClient):
        """Test classifying an eligible product."""
        response = await async_client.post(
            "/classify",
            json={
                "product_id": "API-001",
                "product_name": "Fresh Organic Apples",
                "category": "Produce",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["is_ebt_eligible"] is True
        assert data["classification_category"] == "ELIGIBLE_STAPLE_FOOD"
        assert "audit_id" in data
        assert "confidence_score" in data

    @pytest.mark.asyncio
    async def test_classify_ineligible_alcohol(self, async_client: AsyncClient):
        """Test classifying an ineligible alcohol product."""
        response = await async_client.post(
            "/classify",
            json={
                "product_id": "API-002",
                "product_name": "Budweiser Beer",
                "category": "Beverages",
                "alcohol_content": 0.05,
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["is_ebt_eligible"] is False
        assert data["classification_category"] == "INELIGIBLE_ALCOHOL"

    @pytest.mark.asyncio
    async def test_classify_ineligible_tobacco(self, async_client: AsyncClient):
        """Test classifying an ineligible tobacco product."""
        response = await async_client.post(
            "/classify",
            json={
                "product_id": "API-003",
                "product_name": "Marlboro Cigarettes",
                "category": "Tobacco",
                "contains_tobacco": True,
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["is_ebt_eligible"] is False
        assert data["classification_category"] == "INELIGIBLE_TOBACCO"

    @pytest.mark.asyncio
    async def test_classify_ineligible_supplement(self, async_client: AsyncClient):
        """Test classifying an ineligible supplement."""
        response = await async_client.post(
            "/classify",
            json={
                "product_id": "API-004",
                "product_name": "Centrum Multivitamin",
                "category": "Health",
                "nutrition_label_type": "supplement_facts",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["is_ebt_eligible"] is False
        assert data["classification_category"] == "INELIGIBLE_SUPPLEMENT"

    @pytest.mark.asyncio
    async def test_classify_ineligible_hot_food(self, async_client: AsyncClient):
        """Test classifying an ineligible hot food."""
        response = await async_client.post(
            "/classify",
            json={
                "product_id": "API-005",
                "product_name": "Hot Pizza Slice",
                "category": "Prepared Foods",
                "is_hot_at_sale": True,
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["is_ebt_eligible"] is False
        assert data["classification_category"] == "INELIGIBLE_HOT_FOOD"

    @pytest.mark.asyncio
    async def test_classify_eligible_dairy(self, async_client: AsyncClient):
        """Test classifying eligible dairy."""
        response = await async_client.post(
            "/classify",
            json={
                "product_id": "API-006",
                "product_name": "Organic Whole Milk",
                "category": "Dairy",
                "nutrition_label_type": "nutrition_facts",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["is_ebt_eligible"] is True
        assert data["classification_category"] == "ELIGIBLE_STAPLE_FOOD"

    @pytest.mark.asyncio
    async def test_classify_eligible_beverage(self, async_client: AsyncClient):
        """Test classifying eligible beverage."""
        response = await async_client.post(
            "/classify",
            json={
                "product_id": "API-007",
                "product_name": "Coca-Cola",
                "category": "Beverages",
                "nutrition_label_type": "nutrition_facts",
                "alcohol_content": 0.0,
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["is_ebt_eligible"] is True
        assert data["classification_category"] == "ELIGIBLE_BEVERAGE"

    @pytest.mark.asyncio
    async def test_classify_missing_required_fields(self, async_client: AsyncClient):
        """Test classify with missing required fields."""
        response = await async_client.post(
            "/classify",
            json={
                "product_id": "API-008",
                # Missing product_name
            },
        )

        assert response.status_code == 422  # Validation error

    @pytest.mark.asyncio
    async def test_classify_returns_reasoning(self, async_client: AsyncClient):
        """Test that classify returns reasoning summary."""
        response = await async_client.post(
            "/classify",
            json={
                "product_id": "API-009",
                "product_name": "Fresh Apples",
                "category": "Produce",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert "reasoning_summary" in data
        assert data["reasoning_summary"] is not None


class TestBulkClassifyEndpoint:
    """Test suite for /classify/bulk endpoint."""

    @pytest.mark.asyncio
    async def test_bulk_classify(self, async_client: AsyncClient):
        """Test bulk classification."""
        response = await async_client.post(
            "/classify/bulk",
            json={
                "products": [
                    {
                        "product_id": "BULK-001",
                        "product_name": "Fresh Apples",
                        "category": "Produce",
                    },
                    {
                        "product_id": "BULK-002",
                        "product_name": "Budweiser Beer",
                        "category": "Beverages",
                        "alcohol_content": 0.05,
                    },
                ],
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["total_products"] == 2
        assert "results" in data
        assert len(data["results"]) == 2

    @pytest.mark.asyncio
    async def test_bulk_classify_with_options(self, async_client: AsyncClient):
        """Test bulk classification with options."""
        response = await async_client.post(
            "/classify/bulk",
            json={
                "products": [
                    {
                        "product_id": "BULK-003",
                        "product_name": "Fresh Bananas",
                        "category": "Produce",
                    },
                ],
                "options": {
                    "parallel_processing": True,
                    "max_concurrent": 5,
                },
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["total_products"] == 1

    @pytest.mark.asyncio
    async def test_bulk_classify_empty_list(self, async_client: AsyncClient):
        """Test bulk classification with empty list."""
        response = await async_client.post(
            "/classify/bulk",
            json={
                "products": [],
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["total_products"] == 0
        assert data["successful"] == 0

    @pytest.mark.asyncio
    async def test_bulk_classify_mixed_eligibility(self, async_client: AsyncClient):
        """Test bulk classification returns correct eligibility counts."""
        response = await async_client.post(
            "/classify/bulk",
            json={
                "products": [
                    {
                        "product_id": "MIX-001",
                        "product_name": "Fresh Apples",
                        "category": "Produce",
                    },
                    {
                        "product_id": "MIX-002",
                        "product_name": "Wine",
                        "category": "Beverages",
                        "alcohol_content": 0.12,
                    },
                    {
                        "product_id": "MIX-003",
                        "product_name": "Cheerios",
                        "category": "Cereals",
                        "nutrition_label_type": "nutrition_facts",
                    },
                ],
            },
        )

        assert response.status_code == 200
        data = response.json()
        results = data["results"]

        eligible_count = sum(1 for r in results if r["is_ebt_eligible"])
        ineligible_count = sum(1 for r in results if not r["is_ebt_eligible"])

        assert eligible_count == 2
        assert ineligible_count == 1


class TestExplainEndpoint:
    """Test suite for /explain endpoint."""

    @pytest.mark.asyncio
    async def test_explain_valid_audit_id(self, async_client: AsyncClient):
        """Test explain with valid audit ID."""
        # First classify a product to get an audit ID
        classify_response = await async_client.post(
            "/classify",
            json={
                "product_id": "EXP-001",
                "product_name": "Fresh Apples",
                "category": "Produce",
            },
        )

        assert classify_response.status_code == 200
        audit_id = classify_response.json()["audit_id"]

        # Now explain
        explain_response = await async_client.get(f"/explain/{audit_id}")

        assert explain_response.status_code == 200
        data = explain_response.json()
        assert "classification" in data
        assert "explanation" in data
        assert "product" in data

    @pytest.mark.asyncio
    async def test_explain_invalid_audit_id(self, async_client: AsyncClient):
        """Test explain with invalid audit ID."""
        response = await async_client.get("/explain/nonexistent-audit-id-12345")

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_explain_contains_reasoning_chain(self, async_client: AsyncClient):
        """Test that explain contains reasoning chain."""
        # First classify
        classify_response = await async_client.post(
            "/classify",
            json={
                "product_id": "EXP-002",
                "product_name": "Budweiser Beer",
                "alcohol_content": 0.05,
            },
        )

        audit_id = classify_response.json()["audit_id"]

        # Explain
        explain_response = await async_client.get(f"/explain/{audit_id}")

        assert explain_response.status_code == 200
        data = explain_response.json()
        assert "explanation" in data
        explanation = data["explanation"]
        assert "reasoning_chain" in explanation


class TestAuditTrailEndpoint:
    """Test suite for /audit-trail endpoint."""

    @pytest.mark.asyncio
    async def test_audit_trail_list(self, async_client: AsyncClient):
        """Test listing audit trail."""
        # Create some classifications first
        await async_client.post(
            "/classify",
            json={
                "product_id": "AUD-001",
                "product_name": "Fresh Apples",
                "category": "Produce",
            },
        )

        response = await async_client.get("/audit-trail")

        assert response.status_code == 200
        data = response.json()
        assert "records" in data
        assert "total_records" in data

    @pytest.mark.asyncio
    async def test_audit_trail_with_filters(self, async_client: AsyncClient):
        """Test audit trail with filters."""
        response = await async_client.get(
            "/audit-trail",
            params={
                "limit": 10,
                "is_ebt_eligible": True,
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert "records" in data

    @pytest.mark.asyncio
    async def test_audit_trail_stats(self, async_client: AsyncClient):
        """Test audit trail statistics endpoint."""
        response = await async_client.get("/audit-trail/stats")

        assert response.status_code == 200
        data = response.json()
        assert "total_classifications" in data


class TestChallengeEndpoint:
    """Test suite for /challenge endpoint."""

    @pytest.mark.asyncio
    async def test_challenge_classification(self, async_client: AsyncClient):
        """Test challenging a classification."""
        # First classify
        classify_response = await async_client.post(
            "/classify",
            json={
                "product_id": "CHL-001",
                "product_name": "Mystery Beverage",
                "category": "Beverages",
            },
        )

        audit_id = classify_response.json()["audit_id"]

        # Challenge
        challenge_response = await async_client.post(
            f"/challenge/{audit_id}",
            json={
                "challenge_reason": "This product should be classified differently based on its actual ingredients.",
                "additional_evidence": {
                    "new_description": "This is actually a non-alcoholic beverage",
                },
            },
        )

        assert challenge_response.status_code == 200
        data = challenge_response.json()
        assert "original_classification" in data
        assert "new_classification" in data

    @pytest.mark.asyncio
    async def test_challenge_invalid_audit_id(self, async_client: AsyncClient):
        """Test challenging with invalid audit ID."""
        response = await async_client.post(
            "/challenge/nonexistent-id",
            json={
                "challenge_reason": "Test challenge reason that is long enough",
            },
        )

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_challenge_missing_reason(self, async_client: AsyncClient):
        """Test challenge without reason."""
        # First classify
        classify_response = await async_client.post(
            "/classify",
            json={
                "product_id": "CHL-002",
                "product_name": "Test Product",
                "category": "Produce",
            },
        )

        audit_id = classify_response.json()["audit_id"]

        # Challenge without reason
        challenge_response = await async_client.post(
            f"/challenge/{audit_id}",
            json={},
        )

        assert challenge_response.status_code == 422  # Validation error


class TestHealthEndpoint:
    """Test suite for health endpoint."""

    @pytest.mark.asyncio
    async def test_health_check(self, async_client: AsyncClient):
        """Test health check endpoint."""
        response = await async_client.get("/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
