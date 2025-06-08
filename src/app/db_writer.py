"""Writes processed analysis data to PostgreSQL with batching and retries."""

from typing import Any

import psycopg2
from psycopg2.extras import Json, execute_batch
from psycopg2.pool import ThreadedConnectionPool
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_fixed

from app.config import get_postgres_dsn, get_postgres_table
from app.utils.setup_logger import setup_logger

logger = setup_logger(__name__)

# Connection pool
_pool: ThreadedConnectionPool | None = None


def _get_connection():
    global _pool
    if _pool is None:
        logger.info("🔌 Initializing PostgreSQL connection pool...")
        _pool = ThreadedConnectionPool(minconn=1, maxconn=5, dsn=get_postgres_dsn())
    return _pool.getconn()


def _release_connection(conn):
    if _pool:
        _pool.putconn(conn)


@retry(
    retry=retry_if_exception_type((psycopg2.OperationalError, psycopg2.InterfaceError)),
    wait=wait_fixed(5),
    stop=stop_after_attempt(5),
)
def write_batch_to_postgres(data_batch: list[dict[str, Any]]) -> None:
    """Writes a batch of analysis results to PostgreSQL."""
    if not data_batch:
        logger.warning("🟡 No data to write to PostgreSQL.")
        return

    conn = None
    cur = None
    try:
        conn = _get_connection()
        cur = conn.cursor()

        insert_query = f"""
            INSERT INTO {get_postgres_table()} (symbol, source, timestamp, data)
            VALUES (%s, %s, %s, %s)
        """

        records = [
            (
                record.get("symbol"),
                record.get("source", "unknown"),
                record.get("timestamp"),
                Json(record.get("analysis")),
            )
            for record in data_batch
        ]

        execute_batch(cur, insert_query, records)
        conn.commit()
        logger.info("✅ Wrote %d records to PostgreSQL", len(records))

    except Exception as e:
        logger.exception("❌ Failed to write batch to PostgreSQL: %s", e)
        raise

    finally:
        if cur:
            try:
                cur.close()
            except Exception:
                logger.warning("⚠️ Failed to close cursor.")
        if conn:
            try:
                _release_connection(conn)
            except Exception:
                logger.warning("⚠️ Failed to release PostgreSQL connection.")
