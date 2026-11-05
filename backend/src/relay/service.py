"""Assembly: turn raw per-day tallies into the dashboard payload.

`stats.py` owns the judgement, `repository.py` owns the SQL, this module owns the
composition (windows, coverage, drivers, data-quality notes) and nothing else.
"""

from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import dataclass
from datetime import UTC, date, datetime
from typing import Protocol

from . import stats
from .models import (
    AccountRef,
    AccountsResponse,
    AccountSummary,
    DashboardResponse,
    Driver,
    Headline,
    InProgress,
    LocationRow,
    MetricModel,
    Note,
    Period,
    SeriesPointModel,
)
from .narrative import (
    NarrativeContext,
    NarrativeDriver,
    Narrator,
    TemplateNarrator,
    format_number,
    format_range,
    format_value,
)
from .stats import MetricResult, Tally, Window

DEFAULT_BASELINE_WEEKS = 8
MAX_BASELINE_WEEKS = 26
MAX_DRIVERS = 3
STALE_AFTER_DAYS = 1
STALE_WARNING_DAYS = 7

HEADLINES = {
    ("last_week", stats.WITHIN): "Last week looked normal",
    ("last_week", stats.ABOVE): "Last week was busier than usual",
    ("last_week", stats.BELOW): "Last week was quieter than usual",
    ("last_week", stats.INSUFFICIENT): "Not enough history to tell yet",
    ("this_week", stats.WITHIN): "This week looks normal so far",
    ("this_week", stats.ABOVE): "This week is busier than usual so far",
    ("this_week", stats.BELOW): "This week is quieter than usual so far",
    (None, stats.NO_ACTIVITY): "No activity yet",
}

#: A partial window needs at least this many days before it can lead the headline.
MIN_HEADLINE_DAYS = 2


@dataclass(frozen=True)
class AccountRow:
    """One row of `accounts` plus the cheap aggregates the roster needs."""

    id: int
    name: str
    industry: str
    timezone: str
    created_local: date
    first_event_local: date | None
    last_event_local: date | None
    last_event_at: datetime | None
    locations: tuple[str, ...]
    event_count: int


@dataclass(frozen=True)
class DayRow:
    day: date
    location: str
    tally: Tally


class Repository(Protocol):
    def data_through(self) -> date | None: ...

    def accounts(self) -> list[AccountRow]: ...

    def account(self, account_id: int) -> AccountRow | None: ...

    def day_rows(self, account: AccountRow, day_from: date, day_to: date) -> list[DayRow]: ...


class AccountNotFound(LookupError):
    pass


class DataUnavailable(RuntimeError):
    """Nothing to analyse: the database holds no events at all."""


def _clamp_baseline_weeks(value: int | None, default: int) -> int:
    weeks = default if value is None else value
    return max(1, min(MAX_BASELINE_WEEKS, weeks))


def day_label(day: date) -> str:
    return f"{day.strftime('%b')} {day.day}"


def range_label(start: date, end: date) -> str:
    if start == end:
        return day_label(start)
    return f"{day_label(start)} – {day_label(end)}"


def _build_series(rows: Sequence[DayRow]) -> stats.DayTallies:
    series: stats.DayTallies = {}
    for row in rows:
        series.setdefault(row.day, {})[row.location] = row.tally
    return series


def _coverage_note(metric: MetricResult, tally: Tally) -> str | None:
    if metric.key == "missed_call_rate" and tally.calls > tally.calls_with_outcome:
        missing = tally.calls - tally.calls_with_outcome
        return (
            f"{missing:,} of {tally.calls:,} calls had no outcome and are "
            "excluded from this rate."
        )
    if metric.key == "no_show_rate" and tally.appointments > tally.appointments_with_outcome:
        missing = tally.appointments - tally.appointments_with_outcome
        return (
            f"{missing:,} of {tally.appointments:,} appointments had no outcome "
            "and are excluded from this rate."
        )
    return None


def _metric_model(result: MetricResult) -> MetricModel:
    return MetricModel(
        key=result.key,
        label=result.label,
        unit=result.unit,
        kind=result.kind,
        status=result.status,
        current=result.current,
        typical=result.typical,
        low=result.low,
        high=result.high,
        delta=result.delta,
        ratio=result.ratio,
        numerator=result.numerator,
        denominator=result.denominator,
        series=[
            SeriesPointModel(
                week_start=point.week_start, value=point.value, current=point.current
            )
            for point in result.series
        ],
        note=result.note,
    )


class DashboardService:
    def __init__(
        self,
        repository: Repository,
        *,
        baseline_weeks: int = DEFAULT_BASELINE_WEEKS,
        narrator: Narrator | None = None,
        today: Callable[[], date] | None = None,
        now: Callable[[], datetime] | None = None,
    ) -> None:
        self._repository = repository
        self._baseline_weeks = _clamp_baseline_weeks(baseline_weeks, DEFAULT_BASELINE_WEEKS)
        self._narrator = narrator or TemplateNarrator()
        self._today = today or (lambda: datetime.now(UTC).date())
        self._now = now or (lambda: datetime.now(UTC))

    # -- roster ------------------------------------------------------------
    def list_accounts(self) -> AccountsResponse:
        accounts = self._repository.accounts()
        return AccountsResponse(
            data_through=self._repository.data_through(),
            accounts=[
                AccountSummary(
                    id=account.id,
                    name=account.name,
                    industry=account.industry,
                    timezone=account.timezone,
                    locations=list(account.locations),
                    last_event_at=account.last_event_at,
                    event_count=account.event_count,
                )
                for account in accounts
            ],
        )

    # -- dashboard ---------------------------------------------------------
    def dashboard(
        self,
        account_id: int,
        *,
        as_of: date | None = None,
        baseline_weeks: int | None = None,
    ) -> DashboardResponse:
        account = self._repository.account(account_id)
        if account is None:
            raise AccountNotFound(account_id)

        latest_day = self._repository.data_through()
        if latest_day is None:
            raise DataUnavailable("no activity events in this deployment")

        weeks = _clamp_baseline_weeks(baseline_weeks, self._baseline_weeks)
        anchor = min(as_of, latest_day) if as_of else latest_day
        as_of_source = "requested" if as_of else "latest_data"

        primary = stats.previous_complete_week(stats.last_complete_day(anchor))
        history_start = max(
            account.created_local, account.first_event_local or account.created_local
        )
        empty = account.event_count == 0
        # An account with no events has no history to be normal against: refuse to
        # judge instead of reporting "typical, zero" with a straight face.
        references, skipped = (
            ([], 0) if empty else stats.reference_windows(primary, weeks, history_start)
        )
        fetch_from = min(
            [reference.start for reference in references] or [primary.start]
        )
        rows = self._repository.day_rows(account, fetch_from, anchor)
        series = _build_series(rows)

        window_tally = stats.tally_window(series, primary)
        results: list[MetricResult] = []
        for spec in stats.METRICS:
            result = stats.evaluate_metric(spec, series, primary, references)
            note = _coverage_note(result, window_tally)
            results.append(result if note is None else stats.with_note(result, note))

        metrics = tuple(results)
        activity = metrics[0]

        in_progress = stats.partial_window(primary, anchor)
        in_progress_result: InProgress | None = None
        partial_metrics: tuple[MetricResult, ...] = ()
        partial_locations: list[LocationRow] = []
        if in_progress is not None:
            partial_refs = (
                []
                if empty
                else stats.reference_windows(in_progress, weeks, history_start)[0]
            )
            partial_tally = stats.tally_window(series, in_progress)
            partial_results: list[MetricResult] = []
            for spec in stats.METRICS:
                result = stats.evaluate_metric(spec, series, in_progress, partial_refs)
                note = _coverage_note(result, partial_tally)
                partial_results.append(
                    result if note is None else stats.with_note(result, note)
                )
            partial_metrics = tuple(partial_results)
            if not empty:
                partial_locations, _ = self._locations(
                    account, series, in_progress, partial_refs
                )
            in_progress_result = InProgress(
                start=in_progress.start,
                end=in_progress.end,
                label=f"This week so far ({_days_label(in_progress.day_count)})",
                day_count=in_progress.day_count,
                partial=True,
                metrics=[_metric_model(result) for result in partial_metrics],
            )

        locations, silent = self._locations(account, series, primary, references)

        # The headline answers "is this normal for us *now*". Last week is the stable,
        # comparable view, but when the current week is already clearly out of range we
        # lead with it — a Thursday should not be told "last week was fine".
        basis = "last_week"
        headline_metric = activity
        headline_locations = locations
        headline_metrics = metrics
        if (
            in_progress is not None
            and not empty
            and in_progress.day_count >= MIN_HEADLINE_DAYS
        ):
            candidate = next(
                (result for result in partial_metrics if result.key == "activity"), None
            )
            if candidate is not None and candidate.status in (stats.ABOVE, stats.BELOW):
                basis = "this_week"
                headline_metric = candidate
                headline_locations = partial_locations
                headline_metrics = partial_metrics

        headline_status = stats.NO_ACTIVITY if empty else headline_metric.status
        drivers = self._drivers(headline_locations, headline_status)

        headline = Headline(
            status=headline_status,
            basis=None if empty else basis,
            metric_key="activity",
            title=HEADLINES[(None if empty else basis, headline_status)],
            detail=self._headline_detail(
                headline_metric,
                empty,
                basis=basis,
                window=in_progress if basis == "this_week" else primary,
            ),
        )

        context = NarrativeContext(
            account_name=account.name,
            period_label=range_label(primary.start, primary.end),
            headline_status=headline_status,
            headline_basis=basis,
            metrics=headline_metrics,
            drivers=tuple(
                NarrativeDriver(location=driver.location, delta=driver.delta)
                for driver in drivers
            ),
            location_count=len(account.locations),
            empty=empty,
        )

        return DashboardResponse(
            account=AccountRef(
                id=account.id,
                name=account.name,
                industry=account.industry,
                timezone=account.timezone,
            ),
            generated_at=self._now(),
            data_through=anchor,
            as_of_source=as_of_source,
            staleness_days=max(0, (self._today() - anchor).days),
            empty=empty,
            period=Period(
                start=primary.start,
                end=primary.end,
                label=range_label(primary.start, primary.end),
                day_count=primary.day_count,
                baseline_weeks=weeks,
                reference_weeks_used=(
                    _activity_of(metrics).references_used if _activity_of(metrics) else 0
                ),
                reference_weeks_skipped=skipped,
            ),
            headline=headline,
            metrics=[_metric_model(result) for result in metrics],
            in_progress=in_progress_result,
            locations=locations,
            drivers=drivers,
            narrative=self._narrator.explain(context),
            data_quality=self._notes(
                account=account,
                anchor=anchor,
                primary=primary,
                window_tally=window_tally,
                skipped=skipped,
                silent=silent,
                empty=empty,
                activity=activity,
            ),
        )

    # -- pieces ------------------------------------------------------------
    def _headline_detail(
        self,
        activity: MetricResult,
        empty: bool,
        *,
        basis: str = "last_week",
        window: Window | None = None,
    ) -> str:
        if empty:
            return "We haven't received any events for this account yet."
        if activity.status == stats.INSUFFICIENT:
            usable = len([point for point in activity.series if not point.current])
            return (
                "We need at least 4 comparable weeks of history; this account has "
                f"{usable}."
            )
        if activity.status == stats.NOT_ENOUGH:
            return "Not enough events in this period to compare."
        if activity.low is None or activity.high is None:
            return f"{format_value(activity)} in total."
        unit = "calls" if activity.unit == "calls" else "events"
        if basis == "this_week" and window is not None:
            days = _days_label(window.day_count)
            return (
                f"{format_value(activity)} {unit} so far, against a usual "
                f"{format_range(activity)} over {days}."
            )
        return (
            f"{format_value(activity)} {unit} against a usual "
            f"{format_range(activity)}."
        )

    def _locations(
        self,
        account: AccountRow,
        series: stats.DayTallies,
        window: Window,
        references: Sequence[Window],
    ) -> tuple[list[LocationRow], list[str]]:
        activity_spec = stats.METRICS_BY_KEY["activity"]
        missed_spec = stats.METRICS_BY_KEY["missed_call_rate"]
        no_show_spec = stats.METRICS_BY_KEY["no_show_rate"]

        rows: list[LocationRow] = []
        silent: list[str] = []
        for location in account.locations:
            tally = stats.tally_window(series, window, location)
            activity = stats.evaluate_metric(
                activity_spec, series, window, references, location=location
            )
            missed = stats.evaluate_metric(
                missed_spec, series, window, references, location=location
            )
            no_show = stats.evaluate_metric(
                no_show_spec, series, window, references, location=location
            )
            note = None
            if tally.activity == 0 and activity.status == stats.BELOW:
                note = "No activity in this period."
                silent.append(location)
            rows.append(
                LocationRow(
                    location=location,
                    status=activity.status,
                    current=int(activity.current or 0),
                    typical=activity.typical,
                    low=activity.low,
                    high=activity.high,
                    delta=activity.delta,
                    ratio=activity.ratio,
                    share=None,
                    calls=tally.calls,
                    missed_rate=missed.current,
                    missed_rate_status=missed.status,
                    leads=tally.leads,
                    appointments=tally.appointments,
                    no_show_rate=no_show.current,
                    note=note,
                )
            )

        total_abs = sum(abs(row.delta or 0) for row in rows)
        if total_abs:
            rows = [
                row.model_copy(
                    update={"share": round(abs(row.delta or 0) / total_abs, 4)}
                )
                for row in rows
            ]

        rows.sort(key=lambda row: (-abs(row.delta or 0), row.location))
        return rows, silent

    def _drivers(self, locations: Sequence[LocationRow], headline_status: str) -> list[Driver]:
        if headline_status not in (stats.ABOVE, stats.BELOW):
            return []
        wanted = 1 if headline_status == stats.ABOVE else -1
        movers = [
            row
            for row in locations
            if row.delta is not None and row.delta * wanted > 0 and row.share is not None
        ]
        return [
            Driver(
                location=row.location,
                direction="up" if wanted > 0 else "down",
                delta=row.delta if row.delta is not None else 0,
                ratio=row.ratio,
                share=row.share if row.share is not None else 0.0,
            )
            for row in movers[:MAX_DRIVERS]
        ]

    def _notes(
        self,
        *,
        account: AccountRow,
        anchor: date,
        primary: Window,
        window_tally: Tally,
        skipped: int,
        silent: Sequence[str],
        empty: bool,
        activity: MetricResult,
    ) -> list[Note]:
        notes: list[Note] = []
        staleness = max(0, (self._today() - anchor).days)
        if staleness > STALE_AFTER_DAYS:
            severity = "warning" if staleness > STALE_WARNING_DAYS else "info"
            notes.append(
                Note(
                    code="stale_data",
                    severity=severity,
                    message=(
                        f"This view is based on data through {day_label(anchor)}, "
                        f"{format_number(staleness)} days ago."
                    ),
                )
            )
        if account.last_event_local and account.last_event_local < primary.end:
            notes.append(
                Note(
                    code="no_recent_activity",
                    severity="warning",
                    message=(
                        f"The most recent event for {account.name} was on "
                        f"{day_label(account.last_event_local)}, before the week "
                        "shown above."
                    ),
                )
            )
        if activity.references_dropped:
            dropped = activity.references_dropped
            notes.append(
                Note(
                    code="reference_weeks_excluded",
                    severity="info",
                    message=(
                        f"{dropped} unusually {'high' if dropped == 1 else 'high or low'} "
                        "week(s) were left out of your normal range so a single "
                        "outlier cannot distort it."
                    ),
                )
            )
        if skipped:
            notes.append(
                Note(
                    code="reference_weeks_skipped",
                    severity="info",
                    message=(
                        f"{skipped} earlier weeks were skipped because the account "
                        "had no data then."
                    ),
                )
            )
        missing_outcomes = window_tally.calls - window_tally.calls_with_outcome
        if missing_outcomes > 0:
            coverage = missing_outcomes / window_tally.calls * 100
            notes.append(
                Note(
                    code="outcome_gaps",
                    severity="info" if coverage < 10 else "warning",
                    message=(
                        f"{format_number(missing_outcomes)} of "
                        f"{format_number(window_tally.calls)} calls in this period "
                        f"({coverage:.0f}%) had no recorded outcome, so the "
                        "missed-call rate covers the rest."
                    ),
                )
            )
        if silent:
            listed = ", ".join(sorted(silent)[:4])
            suffix = "" if len(silent) <= 4 else f" and {len(silent) - 4} more"
            notes.append(
                Note(
                    code="location_silent",
                    severity="warning",
                    message=f"No activity in this period at {listed}{suffix}.",
                )
            )
        if empty and not account.locations:
            notes.append(
                Note(
                    code="no_locations",
                    severity="info",
                    message="No locations have reported for this account yet.",
                )
            )
        return notes


def _activity_of(metrics: Sequence[MetricResult]) -> MetricResult | None:
    return next((metric for metric in metrics if metric.key == "activity"), None)


def _days_label(count: int) -> str:
    return "1 day" if count == 1 else f"{count} days"
