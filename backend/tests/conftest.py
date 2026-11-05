"""Shared fixtures and builders for the backend tests."""

from __future__ import annotations

from collections.abc import Iterable, Sequence
from datetime import UTC, date, datetime, timedelta

from relay.service import AccountRow, DashboardService, DayRow
from relay.stats import Tally

TODAY = date(2026, 11, 5)
NOW = datetime(2026, 11, 5, 14, 0, tzinfo=UTC)
ANCHOR = date(2026, 7, 27)  # a Monday: the seed's newest data day
HISTORY_START = date(2026, 2, 1)


def days(start: date, end: date) -> list[date]:
    return [start + timedelta(days=offset) for offset in range((end - start).days + 1)]


def flat_rows(
    start: date,
    end: date,
    *,
    location: str = "Site A",
    tally: Tally | None = None,
    skip: Iterable[date] = (),
) -> list[DayRow]:
    """One DayRow per day, same tally every day."""
    tally = tally or Tally(activity=10, calls=4, calls_with_outcome=4, missed=1)
    skipped = set(skip)
    return [
        DayRow(day=day, location=location, tally=tally)
        for day in days(start, end)
        if day not in skipped
    ]


def week_rows(
    anchor: date,
    *,
    weeks: int = 8,
    per_day: int = 10,
    location: str = "Site A",
    override: dict[date, int] | None = None,
    **tally_fields: int,
) -> list[DayRow]:
    """`weeks` whole weeks of history ending the Sunday before `anchor`."""
    override = override or {}
    tally = Tally(activity=per_day, **tally_fields)
    rows: list[DayRow] = []
    for day in days(anchor - timedelta(days=7 * weeks), anchor):
        activity = override.get(day)
        day_tally = tally if activity is None else Tally(**{**tally_fields, "activity": activity})
        rows.append(DayRow(day=day, location=location, tally=day_tally))
    return rows


def account(
    *,
    account_id: int = 6,
    name: str = "Metro Collision Centers",
    locations: Sequence[str] = ("Site A",),
    created_local: date = date(2025, 4, 22),
    first_event_local: date | None = HISTORY_START,
    last_event_local: date | None = ANCHOR,
    event_count: int | None = None,
) -> AccountRow:
    return AccountRow(
        id=account_id,
        name=name,
        industry="Automotive Services",
        timezone="America/Chicago",
        created_local=created_local,
        first_event_local=first_event_local,
        last_event_local=last_event_local,
        last_event_at=(
            datetime.combine(last_event_local, datetime.min.time(), tzinfo=UTC)
            if last_event_local
            else None
        ),
        locations=tuple(locations),
        event_count=event_count if event_count is not None else 1000,
    )


class FakeRepository:
    def __init__(
        self,
        *,
        rows: Sequence[DayRow] = (),
        accounts: Sequence[AccountRow] = (),
        data_through: date | None = ANCHOR,
    ) -> None:
        self.rows = list(rows)
        self._accounts = list(accounts)
        self._data_through = data_through

    def data_through(self) -> date | None:
        return self._data_through

    def accounts(self) -> list[AccountRow]:
        return list(self._accounts)

    def account(self, account_id: int) -> AccountRow | None:
        return next((a for a in self._accounts if a.id == account_id), None)

    def day_rows(self, account: AccountRow, day_from: date, day_to: date) -> list[DayRow]:
        return [row for row in self.rows if day_from <= row.day <= day_to]


def make_service(repository: FakeRepository, **kwargs) -> DashboardService:
    return DashboardService(
        repository,
        today=lambda: TODAY,
        now=lambda: NOW,
        **kwargs,
    )
