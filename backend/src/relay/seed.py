"""Seed loader for `seed.sql`.

The seed file is a data export, not a fixture: it contains byte-identical
duplicate events, durations on calls whose outcome says "missed", NULL outcomes,
and one account with no events at all. Loading it raw would bake those artefacts
into every number the dashboard shows, so we validate and normalise it once,
deterministically, and print exactly what was changed.

Rules
-----
* Unknown `event_type` -> hard error (the dashboard cannot speak about it).
* Unknown `account_id`  -> hard error.
* Byte-identical event  -> dropped, one warning line, counted.
* `duration_seconds` on a non-call -> cleared to NULL, counted (duration is only
  meaningful for calls, and even then only for connected ones).
* Everything else is preserved verbatim, including NULLs.
"""

from __future__ import annotations

import argparse
import os
import re
import sys
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path

import psycopg

from .config import DEFAULT_DATABASE_URL

EVENT_TYPES = {"call_received", "lead_created", "appointment_set"}
DURATION_EVENT_TYPES = {"call_received"}
ACCOUNT_COLUMNS = ("id", "name", "industry", "timezone", "created_at")
EVENT_COLUMNS = (
    "id",
    "account_id",
    "location",
    "event_type",
    "occurred_at",
    "duration_seconds",
    "outcome",
)

INSERT_RE = re.compile(
    r"^INSERT\s+INTO\s+(?P<table>\w+)\s*\((?P<columns>[^)]*)\)\s*VALUES\s*\((?P<values>.*)\)\s*$",
    re.IGNORECASE | re.DOTALL,
)


class SeedError(ValueError):
    """The seed file cannot be loaded without guessing."""


@dataclass(frozen=True)
class SeedAccount:
    id: int
    name: str
    industry: str
    timezone: str
    created_at: datetime


@dataclass(frozen=True)
class SeedEventDraft:
    id: int
    account_id: int
    location: str
    event_type: str
    occurred_at: datetime
    duration_seconds: int | None
    outcome: str | None


@dataclass
class LoadReport:
    accounts: int = 0
    events: int = 0
    duplicates: int = 0
    durations_cleared: int = 0
    duplicated_samples: list[int] = field(default_factory=list)
    skipped: bool = False

    def as_lines(self) -> list[str]:
        if self.skipped:
            return ["seed skipped: tables already hold data (use --reset to replace it)"]
        lines = [
            f"accounts loaded: {self.accounts}",
            f"events loaded:   {self.events}",
            f"exact duplicates dropped: {self.duplicates}",
            f"durations cleared on non-call events: {self.durations_cleared}",
        ]
        if self.duplicated_samples:
            sample = ", ".join(str(value) for value in self.duplicated_samples[:5])
            lines.append(f"dropped duplicate ids (first 5): {sample}")
        return lines


# --- parsing ---------------------------------------------------------------


def _statements(text: str):
    """Yield (line_number, statement) for every `;`-terminated statement.

    Line comments are stripped while scanning, so a comment above the first INSERT
    does not become part of the statement (and does not hide it).
    """
    buffer: list[str] = []
    in_string = False
    line = 1
    start_line = 1
    index = 0
    while index < len(text):
        char = text[index]
        if char == "'":
            if in_string and index + 1 < len(text) and text[index + 1] == "'":
                buffer.append("''")
                index += 2
                continue
            in_string = not in_string
            buffer.append(char)
        elif not in_string and char == "-" and text[index : index + 2] == "--":
            end_of_line = text.find("\n", index)
            index = len(text) if end_of_line == -1 else end_of_line
            continue
        elif char == ";" and not in_string:
            statement = "".join(buffer).strip()
            if statement:
                yield start_line, statement
            buffer = []
            start_line = line
        else:
            if not buffer and not char.strip():
                start_line = line + (1 if char == "\n" else 0)
            buffer.append(char)
            if char == "\n":
                line += 1
        index += 1


def _split_values(raw: str) -> list[str]:
    values: list[str] = []
    current: list[str] = []
    in_string = False
    index = 0
    while index < len(raw):
        char = raw[index]
        if char == "'":
            if in_string and index + 1 < len(raw) and raw[index + 1] == "'":
                current.append("''")
                index += 2
                continue
            in_string = not in_string
            current.append(char)
        elif char == "," and not in_string:
            values.append("".join(current).strip())
            current = []
        else:
            current.append(char)
        index += 1
    values.append("".join(current).strip())
    return values


NUMBER_RE = re.compile(r"^-?\d+(?:\.\d+)?$")


def _scalar(token: str) -> str | None:
    """A SQL scalar as text: NULL -> None, strings unquoted, numbers verbatim."""
    if token.upper() == "NULL":
        return None
    if len(token) >= 2 and token[0] == "'" and token[-1] == "'":
        return token[1:-1].replace("''", "'")
    if NUMBER_RE.match(token):
        return token
    raise SeedError(f"unsupported literal: {token!r}")


def _integer(token: str | None, what: str) -> int:
    if token is None:
        raise SeedError(f"{what} may not be NULL")
    try:
        return int(token)
    except ValueError as error:
        raise SeedError(f"{what} is not an integer: {token!r}") from error


def _timestamp(token: str | None) -> datetime:
    value = _scalar(token) if token else None
    try:
        parsed = datetime.fromisoformat(value or "")
    except ValueError as error:
        raise SeedError(f"unparsable timestamp: {token!r}") from error
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=UTC)
    return parsed.astimezone(UTC)


def parse_seed(text: str) -> tuple[list[SeedAccount], list[SeedEventDraft], LoadReport]:
    """Parse, validate and normalise the seed file. Never touches a database."""
    accounts: list[SeedAccount] = []
    events: list[SeedEventDraft] = []
    report = LoadReport()
    seen: set[tuple] = set()

    for line_number, statement in _statements(text):
        if statement.lstrip().startswith("--"):
            continue
        match = INSERT_RE.match(statement)
        if match is None:
            raise SeedError(f"line {line_number}: unsupported statement")
        table = match.group("table").lower()
        columns = [column.strip().lower() for column in match.group("columns").split(",")]
        raw_values = _split_values(match.group("values"))
        if len(columns) != len(raw_values):
            raise SeedError(
                f"line {line_number}: {len(columns)} columns but {len(raw_values)} values"
            )
        row = dict(zip(columns, raw_values, strict=True))

        if table == "accounts":
            accounts.append(_build_account(row, line_number))
        elif table == "activity_events":
            draft, dropped_duration = _build_event(row, line_number, report)
            _add_event(draft, events, seen, report)
            if dropped_duration:
                report.durations_cleared += 1
        else:
            raise SeedError(f"line {line_number}: unexpected table {table!r}")

    account_ids = {account.id for account in accounts}
    for event in events:
        if event.account_id not in account_ids:
            raise SeedError(f"event {event.id} references unknown account {event.account_id}")

    report.accounts = len(accounts)
    report.events = len(events)
    return accounts, events, report


def _build_account(row: dict, line_number: int) -> SeedAccount:
    missing = [column for column in ACCOUNT_COLUMNS if column not in row]
    if missing:
        raise SeedError(f"line {line_number}: account row missing {missing}")
    name = _scalar(row["name"])
    industry = _scalar(row["industry"])
    tz = _scalar(row["timezone"])
    if not name or not industry or not tz:
        raise SeedError(f"line {line_number}: account has an empty required field")
    return SeedAccount(
        id=_integer(_scalar(row["id"]), "accounts.id"),
        name=name,
        industry=industry,
        timezone=tz,
        created_at=_timestamp(row["created_at"]),
    )


def _build_event(row: dict, line_number: int, report: LoadReport) -> tuple[SeedEventDraft, bool]:
    missing = [column for column in EVENT_COLUMNS if column not in row]
    if missing:
        raise SeedError(f"line {line_number}: event row missing {missing}")
    event_type = _scalar(row["event_type"]) or ""
    if event_type not in EVENT_TYPES:
        raise SeedError(f"line {line_number}: unknown event_type {event_type!r}")
    location = _scalar(row["location"]) or ""
    if not location.strip():
        raise SeedError(f"line {line_number}: event has an empty location")

    duration_literal = row["duration_seconds"]
    duration: int | None = None
    cleared = False
    if duration_literal.upper() != "NULL":
        value = _integer(_scalar(duration_literal), "duration_seconds")
        if value < 0:
            raise SeedError(f"line {line_number}: negative duration {value}")
        if event_type in DURATION_EVENT_TYPES:
            duration = value
        else:
            cleared = True
    return (
        SeedEventDraft(
            id=_integer(_scalar(row["id"]), "activity_events.id"),
            account_id=_integer(_scalar(row["account_id"]), "activity_events.account_id"),
            location=location,
            event_type=event_type,
            occurred_at=_timestamp(row["occurred_at"]),
            duration_seconds=duration,
            outcome=_scalar(row["outcome"]),
        ),
        cleared,
    )


def _add_event(
    draft: SeedEventDraft, events: list[SeedEventDraft], seen: set[tuple], report: LoadReport
) -> None:
    identity = (
        draft.account_id,
        draft.location,
        draft.event_type,
        draft.occurred_at,
        draft.duration_seconds,
        draft.outcome,
    )
    if identity in seen:
        report.duplicates += 1
        if len(report.duplicated_samples) < 5:
            report.duplicated_samples.append(draft.id)
        return
    seen.add(identity)
    events.append(draft)


def read_seed(path: Path) -> tuple[list[SeedAccount], list[SeedEventDraft], LoadReport]:
    return parse_seed(path.read_text())


# --- loading ---------------------------------------------------------------

COPY_ACCOUNTS = (
    "COPY accounts (id, name, industry, timezone, created_at) FROM STDIN"
)
COPY_EVENTS = (
    "COPY activity_events (id, account_id, location, event_type, occurred_at, "
    "duration_seconds, outcome) FROM STDIN"
)


def _rows_present(connection: psycopg.Connection) -> int:
    return connection.execute(
        "SELECT (SELECT count(*) FROM accounts) + (SELECT count(*) FROM activity_events)"
    ).fetchone()[0]


def load_seed(
    connection: psycopg.Connection,
    path: Path,
    *,
    reset: bool = False,
    if_empty: bool = False,
    dry_run: bool = False,
) -> LoadReport:
    if dry_run:
        return read_seed(path)[2]
    if if_empty and _rows_present(connection):
        # Restart-safe seeding: never wipe (or even parse over) a populated database.
        return LoadReport(skipped=True)

    accounts, events, report = read_seed(path)

    with connection.transaction():
        if reset:
            connection.execute("TRUNCATE activity_events, accounts RESTART IDENTITY")
        elif _rows_present(connection):
            raise SeedError("tables already hold data; re-run with --reset to replace it")
        with connection.cursor() as cursor:
            with cursor.copy(COPY_ACCOUNTS) as copy:
                for account in accounts:
                    copy.write_row(
                        (
                            account.id,
                            account.name,
                            account.industry,
                            account.timezone,
                            account.created_at,
                        )
                    )
            with cursor.copy(COPY_EVENTS) as copy:
                for event in events:
                    copy.write_row(
                        (
                            event.id,
                            event.account_id,
                            event.location,
                            event.event_type,
                            event.occurred_at,
                            event.duration_seconds,
                            event.outcome,
                        )
                    )
        # The seed carries explicit ids; move the identity sequences past them so
        # future inserts do not collide.
        for table in ("accounts", "activity_events"):
            connection.execute(
                f"SELECT setval(pg_get_serial_sequence('{table}', 'id'), "
                f"coalesce((SELECT max(id) FROM {table}), 1))"
            )
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Load seed.sql into Postgres.")
    parser.add_argument("--seed", type=Path, default=Path("/app/seed.sql"))
    parser.add_argument(
        "--database-url", default=os.environ.get("DATABASE_URL", DEFAULT_DATABASE_URL)
    )
    parser.add_argument("--reset", action="store_true", help="truncate before loading")
    parser.add_argument(
        "--if-empty",
        action="store_true",
        help="skip instead of failing when the tables already hold data",
    )
    parser.add_argument("--dry-run", action="store_true", help="validate without writing")
    args = parser.parse_args(argv)

    if args.dry_run:
        _, _, report = read_seed(args.seed)
        for line in report.as_lines():
            print(line)
        return 0

    with psycopg.connect(args.database_url) as connection:
        report = load_seed(
            connection, args.seed, reset=args.reset, if_empty=args.if_empty
        )
    for line in report.as_lines():
        print(line)
    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
