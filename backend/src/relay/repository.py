"""Postgres access for the dashboard.

One grouped query per screen: the dashboard needs the same nine counts over a date
range, split by location, and nothing else. Day bucketing happens in SQL with
`AT TIME ZONE`, so an event at 2026-07-27T04:00Z belongs to the previous local day
on the west coast — the bug this feature would be useless without.
"""

from __future__ import annotations

from collections.abc import Sequence
from datetime import date

from psycopg.rows import dict_row
from psycopg_pool import ConnectionPool

from .service import AccountRow, DayRow
from .stats import Tally

ACCOUNTS_SQL = """
SELECT
    a.id,
    a.name,
    a.industry,
    a.timezone,
    (a.created_at AT TIME ZONE a.timezone)::date AS created_local,
    s.first_event_local,
    s.last_event_local,
    s.last_event_at,
    s.event_count,
    s.locations
FROM accounts a
LEFT JOIN LATERAL (
    SELECT
        (min(e.occurred_at) AT TIME ZONE a.timezone)::date AS first_event_local,
        (max(e.occurred_at) AT TIME ZONE a.timezone)::date AS last_event_local,
        max(e.occurred_at) AS last_event_at,
        count(*) AS event_count,
        coalesce(
            array_agg(DISTINCT e.location) FILTER (WHERE e.location IS NOT NULL),
            '{}'
        ) AS locations
    FROM activity_events e
    WHERE e.account_id = a.id
) s ON true
ORDER BY a.id
"""

ACCOUNT_SQL = ACCOUNTS_SQL.replace("ORDER BY a.id", "WHERE a.id = %(account_id)s")

DATA_THROUGH_SQL = """
SELECT (max(occurred_at) AT TIME ZONE 'UTC')::date AS day
FROM activity_events
"""

DAY_ROWS_SQL = """
SELECT
    (e.occurred_at AT TIME ZONE %(timezone)s)::date AS day,
    e.location,
    count(*)                                                          AS activity,
    count(*) FILTER (WHERE e.event_type = 'call_received')            AS calls,
    count(*) FILTER (
        WHERE e.event_type = 'call_received' AND e.outcome IS NOT NULL
    )                                                                 AS calls_with_outcome,
    count(*) FILTER (
        WHERE e.event_type = 'call_received' AND e.outcome = 'missed'
    )                                                                 AS missed,
    count(*) FILTER (WHERE e.event_type = 'lead_created')             AS leads,
    count(*) FILTER (WHERE e.event_type = 'appointment_set')          AS appointments,
    count(*) FILTER (
        WHERE e.event_type = 'appointment_set'
          AND e.outcome IN ('completed', 'no_show')
    )                                                                 AS appointments_with_outcome,
    count(*) FILTER (
        WHERE e.event_type = 'appointment_set' AND e.outcome = 'no_show'
    )                                                                 AS no_shows
FROM activity_events e
WHERE e.account_id = %(account_id)s
  AND (e.occurred_at AT TIME ZONE %(timezone)s)::date
      BETWEEN %(day_from)s AND %(day_to)s
GROUP BY 1, 2
ORDER BY 1, 2
"""


def _account_from_row(row: dict) -> AccountRow:
    return AccountRow(
        id=row["id"],
        name=row["name"],
        industry=row["industry"],
        timezone=row["timezone"],
        created_local=row["created_local"],
        first_event_local=row["first_event_local"],
        last_event_local=row["last_event_local"],
        last_event_at=row["last_event_at"],
        locations=tuple(sorted(row["locations"] or ())),
        event_count=int(row["event_count"] or 0),
    )


class PostgresRepository:
    def __init__(self, pool: ConnectionPool) -> None:
        self._pool = pool

    # -- protocol ----------------------------------------------------------
    def data_through(self) -> date | None:
        rows = self._fetch(DATA_THROUGH_SQL, {})
        return rows[0]["day"] if rows else None

    def accounts(self) -> list[AccountRow]:
        return [_account_from_row(row) for row in self._fetch(ACCOUNTS_SQL, {})]

    def account(self, account_id: int) -> AccountRow | None:
        rows = self._fetch(ACCOUNT_SQL, {"account_id": account_id})
        return _account_from_row(rows[0]) if rows else None

    def day_rows(
        self, account: AccountRow, day_from: date, day_to: date
    ) -> list[DayRow]:
        rows = self._fetch(
            DAY_ROWS_SQL,
            {
                "account_id": account.id,
                "timezone": account.timezone,
                "day_from": day_from,
                "day_to": day_to,
            },
        )
        return [
            DayRow(
                day=row["day"],
                location=row["location"],
                tally=Tally(
                    activity=row["activity"],
                    calls=row["calls"],
                    calls_with_outcome=row["calls_with_outcome"],
                    missed=row["missed"],
                    leads=row["leads"],
                    appointments=row["appointments"],
                    appointments_with_outcome=row["appointments_with_outcome"],
                    no_shows=row["no_shows"],
                ),
            )
            for row in rows
        ]

    # -- readiness ---------------------------------------------------------
    def ping(self) -> None:
        with self._pool.connection() as conn:
            conn.execute("SELECT 1")

    # -- helpers -----------------------------------------------------------
    def _fetch(self, sql: str, params: dict) -> Sequence[dict]:
        with self._pool.connection() as conn, conn.cursor(row_factory=dict_row) as cursor:
            cursor.execute(sql, params)
            return cursor.fetchall()
