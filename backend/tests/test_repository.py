"""SQL against a real Postgres. Skipped unless TEST_DATABASE_URL is set."""

from __future__ import annotations

import os
from datetime import date
from pathlib import Path

import psycopg
import pytest
from psycopg_pool import ConnectionPool

from relay.migrate import apply_migrations
from relay.repository import DAY_ROWS_SQL, PostgresRepository
from relay.seed import load_seed

DATABASE_URL = os.environ.get("TEST_DATABASE_URL")
SEED_PATH = Path(__file__).resolve().parents[2] / "seed.sql"

pytestmark = pytest.mark.skipif(
    not DATABASE_URL, reason="TEST_DATABASE_URL is not set"
)


@pytest.fixture(scope="module")
def repository() -> PostgresRepository:
    assert DATABASE_URL
    with psycopg.connect(DATABASE_URL) as connection:
        apply_migrations(connection)
        load_seed(connection, SEED_PATH, reset=True)
    pool = ConnectionPool(DATABASE_URL, min_size=1, max_size=2, open=True)
    try:
        yield PostgresRepository(pool)
    finally:
        pool.close()


def test_migrations_are_idempotent(repository: PostgresRepository) -> None:
    assert DATABASE_URL
    with psycopg.connect(DATABASE_URL) as connection:
        assert apply_migrations(connection) == []


def test_ping(repository: PostgresRepository) -> None:
    repository.ping()


def test_data_through_is_the_newest_event_day(repository: PostgresRepository) -> None:
    assert repository.data_through() == date(2026, 7, 27)


def test_roster_shape(repository: PostgresRepository) -> None:
    accounts = repository.accounts()
    assert len(accounts) == 20
    metro = next(account for account in accounts if account.id == 6)
    assert len(metro.locations) == 15
    assert metro.event_count == 2637  # 4 of the 12 duplicate rows were this account's
    assert metro.created_local == date(2025, 4, 22)

    quiet = next(account for account in accounts if account.id == 20)
    assert quiet.event_count == 0
    assert quiet.locations == ()
    assert quiet.last_event_at is None
    assert quiet.first_event_local is None


def test_unknown_account_is_none(repository: PostgresRepository) -> None:
    assert repository.account(999) is None


def test_day_rows_reproduce_the_june_third_incident(
    repository: PostgresRepository,
) -> None:
    metro = repository.account(6)
    assert metro is not None
    rows = repository.day_rows(metro, date(2026, 6, 3), date(2026, 6, 3))
    assert sum(row.tally.activity for row in rows) == 804  # 805 minus one dropped duplicate
    assert len(rows) == 15
    assert {row.day for row in rows} == {date(2026, 6, 3)}


def test_day_rows_expose_outcome_gaps(repository: PostgresRepository) -> None:
    metro = repository.account(6)
    assert metro is not None
    rows = repository.day_rows(metro, date(2026, 2, 1), date(2026, 7, 27))
    total_calls = sum(row.tally.calls for row in rows)
    with_outcome = sum(row.tally.calls_with_outcome for row in rows)
    assert total_calls == 1597
    assert with_outcome < total_calls  # the dashboard must disclose this gap


def test_day_bucketing_uses_the_account_timezone() -> None:
    assert DATABASE_URL
    with psycopg.connect(DATABASE_URL) as connection:
        try:
            connection.execute(
                "INSERT INTO activity_events "
                "(account_id, location, event_type, occurred_at, duration_seconds, outcome) "
                "VALUES (5, 'Site TZ', 'call_received', "
                "'2026-07-28 02:00:00+00', 60, 'connected')"
            )
            rows = connection.execute(
                DAY_ROWS_SQL,
                {
                    "account_id": 5,
                    "timezone": "America/Los_Angeles",
                    "day_from": date(2026, 7, 27),
                    "day_to": date(2026, 7, 28),
                },
            ).fetchall()
        finally:
            connection.rollback()
    # 02:00Z on Jul 28 is still Jul 27 in Los Angeles.
    site_tz = [row for row in rows if row[1] == "Site TZ"]
    assert len(site_tz) == 1
    assert site_tz[0][0] == date(2026, 7, 27)
    assert all(row[0] <= date(2026, 7, 27) for row in rows)
