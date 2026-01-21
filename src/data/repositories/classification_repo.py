"""Repository for classification data operations."""

import json
from datetime import datetime
from typing import Optional

from src.core.constants import ClassificationCategory
from src.data.database import Database, get_database
from src.models.classification import ClassificationResult
from src.models.regulation import RegulationCitation
from src.utils.logging import get_logger

logger = get_logger(__name__)


class ClassificationRepository:
    """Repository for classification CRUD operations."""

    def __init__(self, db: Database = None):
        """
        Initialize repository.

        Args:
            db: Database instance
        """
        self.db = db or get_database()

    async def save(self, result: ClassificationResult) -> None:
        """
        Save a classification result.

        Args:
            result: Classification result to save
        """
        query = """
            INSERT INTO classifications (
                audit_id, product_id, is_ebt_eligible, confidence_score,
                classification_category, reasoning_chain_json,
                regulation_citations_json, key_factors_json,
                model_version, processing_time_ms, classified_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(audit_id) DO UPDATE SET
                is_ebt_eligible = excluded.is_ebt_eligible,
                confidence_score = excluded.confidence_score,
                classification_category = excluded.classification_category,
                reasoning_chain_json = excluded.reasoning_chain_json,
                regulation_citations_json = excluded.regulation_citations_json,
                key_factors_json = excluded.key_factors_json
        """

        citations_json = json.dumps(
            [c.model_dump() for c in result.regulation_citations]
        )

        async with self.db.connection() as conn:
            await conn.execute(
                query,
                (
                    result.audit_id,
                    result.product_id,
                    result.is_ebt_eligible,
                    result.confidence_score,
                    result.classification_category.value,
                    json.dumps(result.reasoning_chain),
                    citations_json,
                    json.dumps(result.key_factors),
                    result.model_version,
                    result.processing_time_ms,
                    result.classification_timestamp.isoformat(),
                ),
            )
            await conn.commit()

        logger.info(
            "classification_saved",
            audit_id=result.audit_id,
            product_id=result.product_id,
        )

    async def get_by_audit_id(self, audit_id: str) -> Optional[ClassificationResult]:
        """
        Get a classification by audit ID.

        Args:
            audit_id: Audit identifier

        Returns:
            ClassificationResult if found, None otherwise
        """
        query = """
            SELECT c.*, p.product_name
            FROM classifications c
            JOIN products p ON c.product_id = p.product_id
            WHERE c.audit_id = ?
        """

        row = await self.db.fetch_one(query, (audit_id,))

        if row:
            return self._row_to_result(row)

        return None

    async def get_by_product_id(
        self,
        product_id: str,
    ) -> Optional[ClassificationResult]:
        """
        Get the latest classification for a product.

        Args:
            product_id: Product identifier

        Returns:
            Most recent ClassificationResult if found, None otherwise
        """
        query = """
            SELECT c.*, p.product_name
            FROM classifications c
            JOIN products p ON c.product_id = p.product_id
            WHERE c.product_id = ?
            ORDER BY c.classified_at DESC
            LIMIT 1
        """

        row = await self.db.fetch_one(query, (product_id,))

        if row:
            return self._row_to_result(row)

        return None

    async def get_all(
        self,
        limit: int = 100,
        offset: int = 0,
        is_eligible: Optional[bool] = None,
        category: Optional[str] = None,
    ) -> list[ClassificationResult]:
        """
        Get all classifications with filters.

        Args:
            limit: Maximum records to return
            offset: Number of records to skip
            is_eligible: Optional eligibility filter
            category: Optional category filter

        Returns:
            List of ClassificationResult objects
        """
        conditions = []
        params = []

        if is_eligible is not None:
            conditions.append("c.is_ebt_eligible = ?")
            params.append(is_eligible)

        if category:
            conditions.append("c.classification_category = ?")
            params.append(category)

        where_clause = ""
        if conditions:
            where_clause = "WHERE " + " AND ".join(conditions)

        query = f"""
            SELECT c.*, p.product_name
            FROM classifications c
            JOIN products p ON c.product_id = p.product_id
            {where_clause}
            ORDER BY c.classified_at DESC
            LIMIT ? OFFSET ?
        """

        params.extend([limit, offset])
        rows = await self.db.fetch_all(query, tuple(params))

        return [self._row_to_result(row) for row in rows]

    async def count(
        self,
        is_eligible: Optional[bool] = None,
        category: Optional[str] = None,
    ) -> int:
        """
        Count classifications with optional filters.

        Args:
            is_eligible: Optional eligibility filter
            category: Optional category filter

        Returns:
            Total count
        """
        conditions = []
        params = []

        if is_eligible is not None:
            conditions.append("is_ebt_eligible = ?")
            params.append(is_eligible)

        if category:
            conditions.append("classification_category = ?")
            params.append(category)

        where_clause = ""
        if conditions:
            where_clause = "WHERE " + " AND ".join(conditions)

        query = f"SELECT COUNT(*) as count FROM classifications {where_clause}"

        row = await self.db.fetch_one(query, tuple(params))
        return row["count"] if row else 0

    def _row_to_result(self, row: dict) -> ClassificationResult:
        """
        Convert a database row to ClassificationResult.

        Args:
            row: Database row dict

        Returns:
            ClassificationResult instance
        """
        citations_data = json.loads(row["regulation_citations_json"])
        citations = [RegulationCitation(**c) for c in citations_data]

        return ClassificationResult(
            product_id=row["product_id"],
            product_name=row["product_name"],
            is_ebt_eligible=bool(row["is_ebt_eligible"]),
            confidence_score=row["confidence_score"],
            classification_category=ClassificationCategory(row["classification_category"]),
            reasoning_chain=json.loads(row["reasoning_chain_json"]),
            regulation_citations=citations,
            key_factors=json.loads(row["key_factors_json"]),
            classification_timestamp=datetime.fromisoformat(row["classified_at"]),
            model_version=row["model_version"],
            processing_time_ms=row["processing_time_ms"] or 0,
            data_sources_used=[],
            audit_id=row["audit_id"],
            request_hash="",
        )
