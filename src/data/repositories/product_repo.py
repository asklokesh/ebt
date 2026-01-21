"""Repository for product data operations."""

import json
from datetime import datetime
from typing import Optional

from src.data.database import Database, get_database
from src.models.product import ProductInput
from src.utils.logging import get_logger

logger = get_logger(__name__)


class ProductRepository:
    """Repository for product CRUD operations."""

    def __init__(self, db: Database = None):
        """
        Initialize repository.

        Args:
            db: Database instance
        """
        self.db = db or get_database()

    async def save(self, product: ProductInput) -> None:
        """
        Save or update a product.

        Args:
            product: Product input to save
        """
        raw_json = json.dumps(product.model_dump())

        query = """
            INSERT INTO products (
                product_id, product_name, upc, category, brand,
                description, raw_input_json, updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(product_id) DO UPDATE SET
                product_name = excluded.product_name,
                upc = excluded.upc,
                category = excluded.category,
                brand = excluded.brand,
                description = excluded.description,
                raw_input_json = excluded.raw_input_json,
                updated_at = excluded.updated_at
        """

        async with self.db.connection() as conn:
            await conn.execute(
                query,
                (
                    product.product_id,
                    product.product_name,
                    product.upc,
                    product.category,
                    product.brand,
                    product.description,
                    raw_json,
                    datetime.utcnow().isoformat(),
                ),
            )
            await conn.commit()

        logger.info("product_saved", product_id=product.product_id)

    async def get_by_id(self, product_id: str) -> Optional[ProductInput]:
        """
        Get a product by ID.

        Args:
            product_id: Product identifier

        Returns:
            ProductInput if found, None otherwise
        """
        query = "SELECT raw_input_json FROM products WHERE product_id = ?"

        row = await self.db.fetch_one(query, (product_id,))

        if row:
            data = json.loads(row["raw_input_json"])
            return ProductInput(**data)

        return None

    async def get_by_upc(self, upc: str) -> Optional[ProductInput]:
        """
        Get a product by UPC.

        Args:
            upc: Universal Product Code

        Returns:
            ProductInput if found, None otherwise
        """
        query = "SELECT raw_input_json FROM products WHERE upc = ?"

        row = await self.db.fetch_one(query, (upc,))

        if row:
            data = json.loads(row["raw_input_json"])
            return ProductInput(**data)

        return None

    async def exists(self, product_id: str) -> bool:
        """
        Check if a product exists.

        Args:
            product_id: Product identifier

        Returns:
            True if product exists
        """
        query = "SELECT 1 FROM products WHERE product_id = ?"
        row = await self.db.fetch_one(query, (product_id,))
        return row is not None

    async def get_all(
        self,
        limit: int = 100,
        offset: int = 0,
        category: Optional[str] = None,
    ) -> list[ProductInput]:
        """
        Get all products with pagination.

        Args:
            limit: Maximum records to return
            offset: Number of records to skip
            category: Optional category filter

        Returns:
            List of ProductInput objects
        """
        if category:
            query = """
                SELECT raw_input_json FROM products
                WHERE category = ?
                ORDER BY updated_at DESC
                LIMIT ? OFFSET ?
            """
            rows = await self.db.fetch_all(query, (category, limit, offset))
        else:
            query = """
                SELECT raw_input_json FROM products
                ORDER BY updated_at DESC
                LIMIT ? OFFSET ?
            """
            rows = await self.db.fetch_all(query, (limit, offset))

        return [ProductInput(**json.loads(row["raw_input_json"])) for row in rows]

    async def count(self, category: Optional[str] = None) -> int:
        """
        Count total products.

        Args:
            category: Optional category filter

        Returns:
            Total count
        """
        if category:
            query = "SELECT COUNT(*) as count FROM products WHERE category = ?"
            row = await self.db.fetch_one(query, (category,))
        else:
            query = "SELECT COUNT(*) as count FROM products"
            row = await self.db.fetch_one(query)

        return row["count"] if row else 0

    async def delete(self, product_id: str) -> bool:
        """
        Delete a product.

        Args:
            product_id: Product identifier

        Returns:
            True if deleted, False if not found
        """
        query = "DELETE FROM products WHERE product_id = ?"

        async with self.db.connection() as conn:
            cursor = await conn.execute(query, (product_id,))
            await conn.commit()
            return cursor.rowcount > 0
