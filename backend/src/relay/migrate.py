"""Tiny forward-only migration runner.

Plain SQL files, applied once, recorded in `schema_migrations`. No ORM, no
autogenerate: the schema is four columns of intent and one grouped query, so the
value of a migration framework here is auditability, not code generation.
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

import psycopg

from .config import DEFAULT_DATABASE_URL

DEFAULT_MIGRATIONS_DIR = Path(__file__).resolve().parents[2] / "migrations"

BOOTSTRAP_SQL = """
CREATE TABLE IF NOT EXISTS schema_migrations (
    version     text        PRIMARY KEY,
    applied_at  timestamptz NOT NULL DEFAULT now()
)
"""


def migrations_dir() -> Path:
    configured = os.environ.get("MIGRATIONS_DIR")
    return Path(configured) if configured else DEFAULT_MIGRATIONS_DIR


def apply_migrations(connection: psycopg.Connection, directory: Path | None = None) -> list[str]:
    directory = directory or migrations_dir()
    connection.execute(BOOTSTRAP_SQL)
    connection.commit()
    applied = {
        row[0] for row in connection.execute("SELECT version FROM schema_migrations").fetchall()
    }
    newly_applied: list[str] = []
    for path in sorted(directory.glob("*.sql")):
        if path.name in applied:
            continue
        with connection.transaction():
            connection.execute(path.read_text())
            connection.execute(
                "INSERT INTO schema_migrations (version) VALUES (%s)", (path.name,)
            )
        newly_applied.append(path.name)
    return newly_applied


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Apply pending SQL migrations.")
    parser.add_argument(
        "--database-url",
        default=os.environ.get("DATABASE_URL", DEFAULT_DATABASE_URL),
    )
    parser.add_argument("--dir", type=Path, default=None)
    args = parser.parse_args(argv)

    with psycopg.connect(args.database_url) as connection:
        applied = apply_migrations(connection, args.dir)
    if applied:
        print(f"applied: {', '.join(applied)}")
    else:
        print("applied: nothing (schema up to date)")
    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
