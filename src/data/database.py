"""SQLite database connection and utilities."""

import os
from contextlib import asynccontextmanager
from pathlib import Path
from typing import AsyncGenerator

import aiosqlite

from src.core.config import settings
from src.core.exceptions import DatabaseError
from src.utils.logging import get_logger

logger = get_logger(__name__)


class Database:
    """Async SQLite database wrapper."""

    def __init__(self, db_path: str = None):
        """
        Initialize database connection.

        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path or settings.database_path
        self._ensure_directory()

    def _ensure_directory(self) -> None:
        """Ensure the database directory exists."""
        db_dir = Path(self.db_path).parent
        db_dir.mkdir(parents=True, exist_ok=True)

    @asynccontextmanager
    async def connection(self) -> AsyncGenerator[aiosqlite.Connection, None]:
        """
        Get an async database connection.

        Yields:
            aiosqlite connection

        Raises:
            DatabaseError: If connection fails
        """
        try:
            async with aiosqlite.connect(self.db_path) as db:
                db.row_factory = aiosqlite.Row
                yield db
        except Exception as e:
            logger.error("database_connection_failed", error=str(e), path=self.db_path)
            raise DatabaseError(f"Failed to connect to database: {e}")

    async def execute(
        self,
        query: str,
        parameters: tuple = (),
    ) -> aiosqlite.Cursor:
        """
        Execute a single query.

        Args:
            query: SQL query
            parameters: Query parameters

        Returns:
            Cursor with results
        """
        async with self.connection() as db:
            cursor = await db.execute(query, parameters)
            await db.commit()
            return cursor

    async def execute_many(
        self,
        query: str,
        parameters_list: list[tuple],
    ) -> None:
        """
        Execute a query with multiple parameter sets.

        Args:
            query: SQL query
            parameters_list: List of parameter tuples
        """
        async with self.connection() as db:
            await db.executemany(query, parameters_list)
            await db.commit()

    async def fetch_one(
        self,
        query: str,
        parameters: tuple = (),
    ) -> dict | None:
        """
        Fetch a single row.

        Args:
            query: SQL query
            parameters: Query parameters

        Returns:
            Row as dict or None
        """
        async with self.connection() as db:
            cursor = await db.execute(query, parameters)
            row = await cursor.fetchone()
            return dict(row) if row else None

    async def fetch_all(
        self,
        query: str,
        parameters: tuple = (),
    ) -> list[dict]:
        """
        Fetch all rows.

        Args:
            query: SQL query
            parameters: Query parameters

        Returns:
            List of rows as dicts
        """
        async with self.connection() as db:
            cursor = await db.execute(query, parameters)
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]

    async def table_exists(self, table_name: str) -> bool:
        """
        Check if a table exists.

        Args:
            table_name: Name of the table

        Returns:
            True if table exists
        """
        query = """
            SELECT name FROM sqlite_master
            WHERE type='table' AND name=?
        """
        result = await self.fetch_one(query, (table_name,))
        return result is not None


# Schema definitions
SCHEMA_SQL = """
-- Products table (cached classifications)
CREATE TABLE IF NOT EXISTS products (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    product_id TEXT UNIQUE NOT NULL,
    product_name TEXT NOT NULL,
    upc TEXT,
    category TEXT,
    brand TEXT,
    description TEXT,
    raw_input_json TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Classifications table
CREATE TABLE IF NOT EXISTS classifications (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    audit_id TEXT UNIQUE NOT NULL,
    product_id TEXT NOT NULL,
    is_ebt_eligible BOOLEAN NOT NULL,
    confidence_score REAL NOT NULL,
    classification_category TEXT NOT NULL,
    reasoning_chain_json TEXT NOT NULL,
    regulation_citations_json TEXT NOT NULL,
    key_factors_json TEXT NOT NULL,
    model_version TEXT NOT NULL,
    processing_time_ms INTEGER,
    classified_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (product_id) REFERENCES products(product_id)
);

-- Audit trail table
CREATE TABLE IF NOT EXISTS audit_trail (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    audit_id TEXT UNIQUE NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    request_payload_json TEXT NOT NULL,
    request_source TEXT NOT NULL,
    classification_result_json TEXT NOT NULL,
    model_used TEXT NOT NULL,
    tokens_consumed INTEGER DEFAULT 0,
    rag_documents_json TEXT,
    was_challenged BOOLEAN DEFAULT FALSE,
    challenge_reason TEXT,
    challenge_result_json TEXT,
    challenge_timestamp TIMESTAMP
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_products_upc ON products(upc);
CREATE INDEX IF NOT EXISTS idx_products_category ON products(category);
CREATE INDEX IF NOT EXISTS idx_classifications_product ON classifications(product_id);
CREATE INDEX IF NOT EXISTS idx_classifications_eligible ON classifications(is_ebt_eligible);
CREATE INDEX IF NOT EXISTS idx_classifications_category ON classifications(classification_category);
CREATE INDEX IF NOT EXISTS idx_audit_timestamp ON audit_trail(timestamp);
CREATE INDEX IF NOT EXISTS idx_audit_challenged ON audit_trail(was_challenged);
"""


async def initialize_database(db: Database = None) -> None:
    """
    Initialize the database schema.

    Args:
        db: Database instance (optional, creates new if not provided)
    """
    if db is None:
        db = Database()

    logger.info("initializing_database", path=db.db_path)

    async with db.connection() as conn:
        await conn.executescript(SCHEMA_SQL)
        await conn.commit()

    logger.info("database_initialized", path=db.db_path)


# Global database instance
_db: Database | None = None


def get_database() -> Database:
    """Get the global database instance."""
    global _db
    if _db is None:
        _db = Database()
    return _db
