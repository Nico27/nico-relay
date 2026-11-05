"""Connection pool factory."""

from __future__ import annotations

from psycopg_pool import ConnectionPool


def create_pool(database_url: str, *, min_size: int = 1, max_size: int = 8) -> ConnectionPool:
    """An open pool. Callers own its lifetime (see `main.create_app`)."""
    pool: ConnectionPool = ConnectionPool(
        conninfo=database_url,
        min_size=min_size,
        max_size=max_size,
        kwargs={"application_name": "relay-dashboard"},
        open=False,
    )
    pool.open(wait=True, timeout=10)
    return pool
