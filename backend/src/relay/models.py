"""Wire models. These mirror `docs/api.md` exactly — the frontend depends on it."""

from __future__ import annotations

from datetime import date, datetime

from pydantic import BaseModel, ConfigDict

Number = int | float


class _Model(BaseModel):
    model_config = ConfigDict(extra="forbid")


class AccountRef(_Model):
    id: int
    name: str
    industry: str
    timezone: str


class AccountSummary(AccountRef):
    locations: list[str]
    last_event_at: datetime | None
    event_count: int


class AccountsResponse(_Model):
    data_through: date | None
    accounts: list[AccountSummary]


class SeriesPointModel(_Model):
    week_start: date
    value: Number
    current: bool


class MetricModel(_Model):
    key: str
    label: str
    unit: str
    kind: str
    status: str
    current: Number | None
    typical: Number | None
    low: Number | None
    high: Number | None
    delta: Number | None
    ratio: float | None
    numerator: int
    denominator: int | None
    series: list[SeriesPointModel]
    note: str | None = None


class Period(_Model):
    start: date
    end: date
    label: str
    day_count: int
    baseline_weeks: int
    reference_weeks_used: int
    reference_weeks_skipped: int


class InProgress(_Model):
    start: date
    end: date
    label: str
    day_count: int
    partial: bool
    metrics: list[MetricModel]


class Headline(_Model):
    status: str
    #: Which window the headline speaks about: "last_week", "this_week", or null when
    #: the account has no activity at all.
    basis: str | None
    metric_key: str
    title: str
    detail: str


class LocationRow(_Model):
    location: str
    status: str
    current: Number
    typical: Number | None
    low: Number | None
    high: Number | None
    delta: Number | None
    ratio: float | None
    share: float | None
    calls: int
    missed_rate: Number | None
    missed_rate_status: str
    leads: int
    appointments: int
    no_show_rate: Number | None
    note: str | None = None


class Driver(_Model):
    location: str
    direction: str
    delta: Number
    ratio: float | None
    share: float


class Note(_Model):
    code: str
    severity: str
    message: str


class DashboardResponse(_Model):
    account: AccountRef
    generated_at: datetime
    data_through: date
    as_of_source: str
    staleness_days: int
    empty: bool
    period: Period
    headline: Headline
    metrics: list[MetricModel]
    in_progress: InProgress | None
    locations: list[LocationRow]
    drivers: list[Driver]
    narrative: str
    data_quality: list[Note]
