"""The seed loader: validation, normalisation, duplicate handling.

The end-to-end load runs in `test_repository.py`; these tests keep the parsing and
cleaning rules honest without a database.
"""

from __future__ import annotations

import os
from datetime import UTC, date, datetime
from pathlib import Path

import pytest

from relay.seed import SeedError, parse_seed, read_seed

SEED_PATH = Path(__file__).resolve().parents[2] / "seed.sql"

ACCOUNT_ROW = (
    "INSERT INTO accounts (id, name, industry, timezone, created_at) "
    "VALUES ({values});"
)
EVENT_ROW = (
    "INSERT INTO activity_events (id, account_id, location, event_type, "
    "occurred_at, duration_seconds, outcome) VALUES ({values});"
)


def seed_sql(*events: str, accounts: str | None = None) -> str:
    account = accounts or ACCOUNT_ROW.format(
        values="1, 'Summit Auto Group', 'Automotive Services', 'America/Chicago', "
        "'2025-05-12 12:00:00'"
    )
    return "-- fixture\n" + account + "\n" + "\n".join(events) + "\n"


def event(values: str) -> str:
    return EVENT_ROW.format(values=values)


def test_parses_accounts_and_events() -> None:
    accounts, events, report = parse_seed(
        seed_sql(
            event(
                "1, 1, 'Site A', 'call_received', '2026-02-01 10:00:00', 120, 'connected'"
            )
        )
    )
    assert accounts[0].name == "Summit Auto Group"
    assert accounts[0].created_at == datetime(2025, 5, 12, 12, tzinfo=UTC)
    assert events[0].occurred_at == datetime(2026, 2, 1, 10, tzinfo=UTC)
    assert events[0].duration_seconds == 120
    assert report.accounts == 1
    assert report.events == 1


def test_byte_identical_events_are_dropped_and_counted() -> None:
    duplicate = (
        "1, 1, 'Site A', 'call_received', '2026-02-01 10:00:00', 120, 'connected'"
    )
    second = (
        "2, 1, 'Site A', 'call_received', '2026-02-01 10:00:00', 120, 'connected'"
    )
    _, events, report = parse_seed(seed_sql(event(duplicate), event(second)))
    assert len(events) == 1
    assert report.duplicates == 1
    assert report.duplicated_samples == [2]


def test_different_outcomes_are_not_duplicates() -> None:
    first = "1, 1, 'Site A', 'call_received', '2026-02-01 10:00:00', 120, 'connected'"
    second = "2, 1, 'Site A', 'call_received', '2026-02-01 10:00:00', 120, 'missed'"
    _, events, report = parse_seed(seed_sql(event(first), event(second)))
    assert len(events) == 2
    assert report.duplicates == 0


def test_duration_is_cleared_for_non_call_events() -> None:
    _, events, report = parse_seed(
        seed_sql(
            event("1, 1, 'Site A', 'lead_created', '2026-02-01 10:00:00', 42, 'open'")
        )
    )
    assert events[0].duration_seconds is None
    assert report.durations_cleared == 1


def test_null_outcome_and_null_duration_survive() -> None:
    _, events, _ = parse_seed(
        seed_sql(
            event(
                "1, 1, 'Site A', 'call_received', '2026-02-01 10:00:00', NULL, NULL"
            )
        )
    )
    assert events[0].duration_seconds is None
    assert events[0].outcome is None


def test_unknown_event_type_is_a_hard_error() -> None:
    with pytest.raises(SeedError, match="unknown event_type"):
        parse_seed(
            seed_sql(
                event("1, 1, 'Site A', 'teleport', '2026-02-01 10:00:00', NULL, NULL")
            )
        )


def test_unknown_account_reference_is_a_hard_error() -> None:
    with pytest.raises(SeedError, match="unknown account"):
        parse_seed(
            seed_sql(
                event(
                    "1, 7, 'Site A', 'lead_created', '2026-02-01 10:00:00', NULL, 'open'"
                )
            )
        )


def test_negative_duration_is_a_hard_error() -> None:
    with pytest.raises(SeedError, match="negative duration"):
        parse_seed(
            seed_sql(
                event(
                    "1, 1, 'Site A', 'call_received', '2026-02-01 10:00:00', -5, 'connected'"
                )
            )
        )


def test_empty_location_is_a_hard_error() -> None:
    with pytest.raises(SeedError, match="empty location"):
        parse_seed(
            seed_sql(
                event(
                    "1, 1, '   ', 'lead_created', '2026-02-01 10:00:00', NULL, 'open'"
                )
            )
        )


def test_quoted_values_with_commas_and_parens_survive() -> None:
    accounts, _, _ = parse_seed(
        ACCOUNT_ROW.format(
            values="9, 'Tire & Service, Inc. (West)', 'Automotive', 'UTC', "
            "'2025-01-01 00:00:00'"
        )
        + "\n"
    )
    assert accounts[0].name == "Tire & Service, Inc. (West)"


def test_the_real_seed_file_loads_and_reports_its_duplicates() -> None:
    accounts, events, report = read_seed(SEED_PATH)
    assert len(accounts) == 20
    assert report.duplicates == 12
    assert report.durations_cleared == 0
    assert len(events) == 12614
    assert min(event.occurred_at for event in events) >= datetime(
        2026, 2, 1, tzinfo=UTC
    )
    # The account with no events must not appear in the event stream.
    assert all(event.account_id != 20 for event in events)
    # Every event belongs to a location and a known type.
    assert {event.event_type for event in events} == {
        "call_received",
        "lead_created",
        "appointment_set",
    }
    assert min(event.occurred_at.date() for event in events) == date(2026, 2, 1)


def test_if_empty_skips_without_error_when_data_exists() -> None:
    """Restart-safe seeding: the container must not wipe a populated database."""
    import psycopg

    from relay.seed import load_seed

    url = os.environ.get("TEST_DATABASE_URL")
    if not url:
        pytest.skip("TEST_DATABASE_URL is not set")
    with psycopg.connect(url) as connection:
        report = load_seed(connection, SEED_PATH, if_empty=True)
    assert report.skipped is True
    assert report.events == 0
    assert "skipped" in report.as_lines()[0]
