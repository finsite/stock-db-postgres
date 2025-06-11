"""Repo-specific configuration for stock-db-postgres."""

from app.config_shared import *


def get_poller_name() -> str:
    """Return the name of the poller for this service."""
    return get_config_value("POLLER_NAME", "stock_db_postgres")


def get_rabbitmq_queue() -> str:
    """Return the RabbitMQ queue name for this poller."""
    return get_config_value("RABBITMQ_QUEUE", "stock_db_postgres_queue")


def get_dlq_name() -> str:
    """Return the Dead Letter Queue (DLQ) name for this poller."""
    return get_config_value("DLQ_NAME", "stock_db_postgres_dlq")

def get_postgres_dsn() -> str:
    """Return the Postgres DSN (Data Source Name)."""
    return get_config_value("POSTGRES_DSN", "postgresql://user:pass@localhost:5432/mydb")


def get_postgres_table() -> str:
    """Return the name of the Postgres table to write to."""
    return get_config_value("POSTGRES_TABLE", "poller_data")