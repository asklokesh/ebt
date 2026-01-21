"""Repository for audit trail operations."""

import json
from datetime import datetime
from typing import Optional

from src.core.constants import ClassificationCategory
from src.data.database import Database, get_database
from src.models.audit import AuditRecord, AuditSummary, AuditTrailQuery
from src.models.classification import ClassificationResult
from src.models.regulation import RegulationCitation
from src.utils.logging import get_logger

logger = get_logger(__name__)


class AuditRepository:
    """Repository for audit trail CRUD operations."""

    def __init__(self, db: Database = None):
        """
        Initialize repository.

        Args:
            db: Database instance
        """
        self.db = db or get_database()

    async def save(self, record: AuditRecord) -> None:
        """
        Save an audit record.

        Args:
            record: Audit record to save
        """
        query = """
            INSERT INTO audit_trail (
                audit_id, timestamp, request_payload_json, request_source,
                classification_result_json, model_used, tokens_consumed,
                rag_documents_json, was_challenged
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(audit_id) DO UPDATE SET
                was_challenged = excluded.was_challenged
        """

        async with self.db.connection() as conn:
            await conn.execute(
                query,
                (
                    record.audit_id,
                    record.timestamp.isoformat(),
                    json.dumps(record.request_payload),
                    record.request_source,
                    record.classification_result.model_dump_json(),
                    record.model_used,
                    record.tokens_consumed,
                    json.dumps(record.rag_documents_retrieved),
                    record.was_challenged,
                ),
            )
            await conn.commit()

        logger.info("audit_record_saved", audit_id=record.audit_id)

    async def get_by_audit_id(self, audit_id: str) -> Optional[AuditRecord]:
        """
        Get an audit record by ID.

        Args:
            audit_id: Audit identifier

        Returns:
            AuditRecord if found, None otherwise
        """
        query = "SELECT * FROM audit_trail WHERE audit_id = ?"

        row = await self.db.fetch_one(query, (audit_id,))

        if row:
            return self._row_to_record(row)

        return None

    async def update_challenge(
        self,
        audit_id: str,
        challenge_reason: str,
        challenge_result: ClassificationResult,
    ) -> None:
        """
        Update an audit record with challenge information.

        Args:
            audit_id: Audit identifier
            challenge_reason: Reason for the challenge
            challenge_result: Result of challenge re-evaluation
        """
        query = """
            UPDATE audit_trail
            SET was_challenged = TRUE,
                challenge_reason = ?,
                challenge_result_json = ?,
                challenge_timestamp = ?
            WHERE audit_id = ?
        """

        async with self.db.connection() as conn:
            await conn.execute(
                query,
                (
                    challenge_reason,
                    challenge_result.model_dump_json(),
                    datetime.utcnow().isoformat(),
                    audit_id,
                ),
            )
            await conn.commit()

        logger.info("audit_challenge_updated", audit_id=audit_id)

    async def query(self, query_params: AuditTrailQuery) -> list[AuditRecord]:
        """
        Query audit records with filters.

        Args:
            query_params: Query parameters

        Returns:
            List of matching AuditRecord objects
        """
        conditions = []
        params = []

        if query_params.start_date:
            conditions.append("timestamp >= ?")
            params.append(query_params.start_date.isoformat())

        if query_params.end_date:
            conditions.append("timestamp <= ?")
            params.append(query_params.end_date.isoformat())

        if query_params.is_ebt_eligible is not None:
            conditions.append(
                "json_extract(classification_result_json, '$.is_ebt_eligible') = ?"
            )
            params.append(query_params.is_ebt_eligible)

        if query_params.classification_category:
            conditions.append(
                "json_extract(classification_result_json, '$.classification_category') = ?"
            )
            params.append(query_params.classification_category)

        if query_params.was_challenged is not None:
            conditions.append("was_challenged = ?")
            params.append(query_params.was_challenged)

        if query_params.product_id:
            conditions.append(
                "json_extract(classification_result_json, '$.product_id') = ?"
            )
            params.append(query_params.product_id)

        where_clause = ""
        if conditions:
            where_clause = "WHERE " + " AND ".join(conditions)

        sql = f"""
            SELECT * FROM audit_trail
            {where_clause}
            ORDER BY timestamp DESC
            LIMIT ? OFFSET ?
        """

        params.extend([query_params.limit, query_params.offset])
        rows = await self.db.fetch_all(sql, tuple(params))

        return [self._row_to_record(row) for row in rows]

    async def get_summaries(
        self,
        query_params: AuditTrailQuery,
    ) -> list[AuditSummary]:
        """
        Get audit summaries with filters.

        Args:
            query_params: Query parameters

        Returns:
            List of AuditSummary objects
        """
        conditions = []
        params = []

        if query_params.start_date:
            conditions.append("timestamp >= ?")
            params.append(query_params.start_date.isoformat())

        if query_params.end_date:
            conditions.append("timestamp <= ?")
            params.append(query_params.end_date.isoformat())

        if query_params.is_ebt_eligible is not None:
            conditions.append(
                "json_extract(classification_result_json, '$.is_ebt_eligible') = ?"
            )
            params.append(query_params.is_ebt_eligible)

        if query_params.classification_category:
            conditions.append(
                "json_extract(classification_result_json, '$.classification_category') = ?"
            )
            params.append(query_params.classification_category)

        if query_params.was_challenged is not None:
            conditions.append("was_challenged = ?")
            params.append(query_params.was_challenged)

        where_clause = ""
        if conditions:
            where_clause = "WHERE " + " AND ".join(conditions)

        sql = f"""
            SELECT
                audit_id,
                timestamp,
                json_extract(classification_result_json, '$.product_id') as product_id,
                json_extract(classification_result_json, '$.product_name') as product_name,
                json_extract(classification_result_json, '$.is_ebt_eligible') as is_ebt_eligible,
                json_extract(classification_result_json, '$.classification_category') as classification_category,
                json_extract(classification_result_json, '$.confidence_score') as confidence_score,
                model_used,
                was_challenged
            FROM audit_trail
            {where_clause}
            ORDER BY timestamp DESC
            LIMIT ? OFFSET ?
        """

        params.extend([query_params.limit, query_params.offset])
        rows = await self.db.fetch_all(sql, tuple(params))

        summaries = []
        for row in rows:
            summaries.append(
                AuditSummary(
                    audit_id=row["audit_id"],
                    timestamp=datetime.fromisoformat(row["timestamp"]),
                    product_id=row["product_id"],
                    product_name=row["product_name"],
                    is_ebt_eligible=bool(row["is_ebt_eligible"]),
                    classification_category=row["classification_category"],
                    confidence_score=row["confidence_score"],
                    model_used=row["model_used"],
                    was_challenged=bool(row["was_challenged"]),
                )
            )

        return summaries

    async def count(self, query_params: AuditTrailQuery) -> int:
        """
        Count audit records matching filters.

        Args:
            query_params: Query parameters

        Returns:
            Total count
        """
        conditions = []
        params = []

        if query_params.start_date:
            conditions.append("timestamp >= ?")
            params.append(query_params.start_date.isoformat())

        if query_params.end_date:
            conditions.append("timestamp <= ?")
            params.append(query_params.end_date.isoformat())

        if query_params.is_ebt_eligible is not None:
            conditions.append(
                "json_extract(classification_result_json, '$.is_ebt_eligible') = ?"
            )
            params.append(query_params.is_ebt_eligible)

        if query_params.was_challenged is not None:
            conditions.append("was_challenged = ?")
            params.append(query_params.was_challenged)

        where_clause = ""
        if conditions:
            where_clause = "WHERE " + " AND ".join(conditions)

        sql = f"SELECT COUNT(*) as count FROM audit_trail {where_clause}"

        row = await self.db.fetch_one(sql, tuple(params))
        return row["count"] if row else 0

    def _row_to_record(self, row: dict) -> AuditRecord:
        """
        Convert a database row to AuditRecord.

        Args:
            row: Database row dict

        Returns:
            AuditRecord instance
        """
        result_data = json.loads(row["classification_result_json"])

        # Reconstruct citations
        citations = [
            RegulationCitation(**c) for c in result_data.get("regulation_citations", [])
        ]

        classification_result = ClassificationResult(
            product_id=result_data["product_id"],
            product_name=result_data["product_name"],
            is_ebt_eligible=result_data["is_ebt_eligible"],
            confidence_score=result_data["confidence_score"],
            classification_category=ClassificationCategory(
                result_data["classification_category"]
            ),
            reasoning_chain=result_data["reasoning_chain"],
            regulation_citations=citations,
            key_factors=result_data.get("key_factors", []),
            classification_timestamp=datetime.fromisoformat(
                result_data["classification_timestamp"]
            ),
            model_version=result_data["model_version"],
            processing_time_ms=result_data.get("processing_time_ms", 0),
            data_sources_used=result_data.get("data_sources_used", []),
            audit_id=result_data["audit_id"],
            request_hash=result_data.get("request_hash", ""),
        )

        # Handle challenge result if present
        challenge_result = None
        if row.get("challenge_result_json"):
            challenge_data = json.loads(row["challenge_result_json"])
            challenge_citations = [
                RegulationCitation(**c)
                for c in challenge_data.get("regulation_citations", [])
            ]
            challenge_result = ClassificationResult(
                product_id=challenge_data["product_id"],
                product_name=challenge_data["product_name"],
                is_ebt_eligible=challenge_data["is_ebt_eligible"],
                confidence_score=challenge_data["confidence_score"],
                classification_category=ClassificationCategory(
                    challenge_data["classification_category"]
                ),
                reasoning_chain=challenge_data["reasoning_chain"],
                regulation_citations=challenge_citations,
                key_factors=challenge_data.get("key_factors", []),
                classification_timestamp=datetime.fromisoformat(
                    challenge_data["classification_timestamp"]
                ),
                model_version=challenge_data["model_version"],
                processing_time_ms=challenge_data.get("processing_time_ms", 0),
                data_sources_used=challenge_data.get("data_sources_used", []),
                audit_id=challenge_data["audit_id"],
                request_hash=challenge_data.get("request_hash", ""),
            )

        return AuditRecord(
            audit_id=row["audit_id"],
            timestamp=datetime.fromisoformat(row["timestamp"]),
            request_payload=json.loads(row["request_payload_json"]),
            request_source=row["request_source"],
            classification_result=classification_result,
            model_used=row["model_used"],
            tokens_consumed=row["tokens_consumed"] or 0,
            rag_documents_retrieved=json.loads(row["rag_documents_json"] or "[]"),
            was_challenged=bool(row["was_challenged"]),
            challenge_reason=row.get("challenge_reason"),
            challenge_result=challenge_result,
            challenge_timestamp=(
                datetime.fromisoformat(row["challenge_timestamp"])
                if row.get("challenge_timestamp")
                else None
            ),
        )
