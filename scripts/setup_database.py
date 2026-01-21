#!/usr/bin/env python3
"""Initialize the SQLite database schema."""

import asyncio
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.data.database import Database, initialize_database


async def main() -> None:
    """Initialize the database."""
    print("Initializing EBT Classification database...")

    db = Database()
    print(f"Database path: {db.db_path}")

    await initialize_database(db)

    # Verify tables were created
    tables = ["products", "classifications", "audit_trail"]
    for table in tables:
        exists = await db.table_exists(table)
        status = "OK" if exists else "MISSING"
        print(f"  Table '{table}': {status}")

    print("Database initialization complete.")


if __name__ == "__main__":
    asyncio.run(main())
