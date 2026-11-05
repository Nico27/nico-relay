"""Baseline statistics for DASH-247 — "is this normal for us?".

Everything in this module is pure: no database, no clock, no I/O, no globals that
change. That is deliberate — the verdict logic is the part of this feature most
likely to be wrong in a way nobody notices, so it must be testable in isolation.

Vocabulary
----------
window       A contiguous run of days in the account's timezone that we judge.
reference    A window of the same weekday set from an earlier week.
typical      The customer's own observed range for that window shape.
"""

from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import dataclass, replace
from datetime import date, timedelta

# --- Tunables ---------------------------------------------------------------
#: Refuse to judge with fewer comparable weeks than this.
MIN_REFERENCE_WEEKS = 4
#: Drop reference weeks further than this many robust sigmas from the median.
OUTLIER_SIGMA = 3.0
#: A rate needs at least this many events in its denominator to be meaningful.
RATE_MIN_DENOMINATOR = 5
#: When a history is perfectly homogeneous (MAD = 0) a single freak week would slip
#: through the sigma test, so we also drop values beyond this multiple of the median.
#: Below this centre the rule is not applied: tiny counts are noisy by nature.
FLAT_HISTORY_MIN_CENTRE = 5.0
#: Rates are compared with this much slack (percentage points) on each side.
RATE_TOLERANCE = 1.0
#: Volumes are compared with this much slack (events) on each side, absorbing
#: the noise of small counts without needing a distributional assumption.
VOLUME_TOLERANCE = 1
#: ...and never less than this share of the median, so a perfectly flat history of
#: 70 events a week does not call 72 "above typical".
VOLUME_RELATIVE_TOLERANCE = 0.10

ABOVE = "above_typical"
WITHIN = "within_typical"
BELOW = "below_typical"
INSUFFICIENT = "insufficient_history"
NOT_ENOUGH = "not_enough_data"
NO_ACTIVITY = "no_activity"

VOLUME = "volume"
RATE = "rate"


@dataclass(frozen=True)
class Tally:
    """Per-day counts for one location (or a whole account).

    The fields exist because each one is a different filter over the same events;
    computing them in one grouped SQL query keeps the dashboard to one round trip.
    """

    activity: int = 0
    calls: int = 0
    calls_with_outcome: int = 0
    missed: int = 0
    leads: int = 0
    appointments: int = 0
    appointments_with_outcome: int = 0
    no_shows: int = 0

    def __add__(self, other: Tally) -> Tally:
        return Tally(
            activity=self.activity + other.activity,
            calls=self.calls + other.calls,
            calls_with_outcome=self.calls_with_outcome + other.calls_with_outcome,
            missed=self.missed + other.missed,
            leads=self.leads + other.leads,
            appointments=self.appointments + other.appointments,
            appointments_with_outcome=(
                self.appointments_with_outcome + other.appointments_with_outcome
            ),
            no_shows=self.no_shows + other.no_shows,
        )


def sum_tallies(tallies: Sequence[Tally]) -> Tally:
    total = Tally()
    for tally in tallies:
        total = total + tally
    return total


@dataclass(frozen=True)
class MetricSpec:
    key: str
    label: str
    unit: str
    kind: str
    numerator: Callable[[Tally], int]
    denominator: Callable[[Tally], int] | None = None
    min_denominator: int = 0

    def value(self, tally: Tally) -> float | None:
        """The metric for a tally, or None when a rate has too small a base."""
        numerator = self.numerator(tally)
        if self.denominator is None:
            return float(numerator)
        denominator = self.denominator(tally)
        if denominator < self.min_denominator:
            return None
        return round(numerator * 100.0 / denominator, 1)


#: The six metrics the dashboard always reports, in display order.
METRICS: tuple[MetricSpec, ...] = (
    MetricSpec("activity", "Activity", "events", VOLUME, lambda t: t.activity),
    MetricSpec("calls", "Calls received", "calls", VOLUME, lambda t: t.calls),
    MetricSpec(
        "missed_call_rate",
        "Missed-call rate",
        "percent",
        RATE,
        lambda t: t.missed,
        lambda t: t.calls_with_outcome,
        RATE_MIN_DENOMINATOR,
    ),
    MetricSpec("leads", "Leads created", "events", VOLUME, lambda t: t.leads),
    MetricSpec("appointments", "Appointments set", "events", VOLUME, lambda t: t.appointments),
    MetricSpec(
        "no_show_rate",
        "No-show rate",
        "percent",
        RATE,
        lambda t: t.no_shows,
        lambda t: t.appointments_with_outcome,
        RATE_MIN_DENOMINATOR,
    ),
)

METRICS_BY_KEY = {metric.key: metric for metric in METRICS}


@dataclass(frozen=True)
class Window:
    start: date
    end: date

    def __post_init__(self) -> None:
        if self.end < self.start:
            raise ValueError(f"window end {self.end} precedes start {self.start}")

    @property
    def day_count(self) -> int:
        return (self.end - self.start).days + 1

    def days(self) -> tuple[date, ...]:
        return tuple(self.start + timedelta(days=offset) for offset in range(self.day_count))


def monday_of(day: date) -> date:
    return day - timedelta(days=day.weekday())


def last_complete_day(anchor: date) -> date:
    """The anchor day itself is never trusted: it may still be filling up."""
    return anchor - timedelta(days=1)


def previous_complete_week(latest_complete_day: date) -> Window:
    """The most recent Monday–Sunday week that ended on or before `latest_complete_day`."""
    end = (
        latest_complete_day
        if latest_complete_day.weekday() == 6
        else monday_of(latest_complete_day) - timedelta(days=1)
    )
    return Window(end - timedelta(days=6), end)


def partial_window(primary: Window, anchor: date) -> Window | None:
    """Days after the judged week, up to the anchor. None when there are none."""
    start = primary.end + timedelta(days=1)
    if start > anchor:
        return None
    return Window(start, anchor)


def reference_windows(
    window: Window, count: int, history_start: date
) -> tuple[list[Window], int]:
    """Same-weekday windows from the preceding weeks, newest first.

    A reference that would start before the account existed (or before our data
    begins) is skipped and counted: a half-empty reference week would otherwise
    look like a genuine drop in activity.
    """
    references: list[Window] = []
    skipped = 0
    for step in range(1, count + 1):
        start = window.start - timedelta(days=7 * step)
        candidate = Window(start, start + timedelta(days=window.day_count - 1))
        if candidate.start < history_start:
            skipped += 1
            continue
        references.append(candidate)
    return references, skipped


@dataclass(frozen=True)
class ReferenceStats:
    median: float
    low: float
    high: float
    used: int
    dropped: int


def median(values: Sequence[float]) -> float:
    ordered = sorted(values)
    middle = len(ordered) // 2
    if len(ordered) % 2:
        return ordered[middle]
    return (ordered[middle - 1] + ordered[middle]) / 2.0


def summarize_references(values: Sequence[float]) -> ReferenceStats | None:
    """Robust centre, robust spread, then an outlier-trimmed observed range.

    The trim matters: one freak week (the seed data has an 805-event day against a
    ~15/day baseline) must not define the customer's "normal" for the next two
    months, or every later change would hide inside an absurdly wide range.
    """
    if not values:
        return None
    centre = median(values)
    sigma = 1.4826 * median([abs(value - centre) for value in values])
    kept = list(values)
    dropped = 0
    if sigma > 0:
        threshold = OUTLIER_SIGMA * sigma
    elif centre >= FLAT_HISTORY_MIN_CENTRE:
        # MAD collapses to zero when nearly every week is identical; without this a
        # single 5x week would silently widen the customer's normal range.
        threshold = centre
    else:
        threshold = float("inf")
    if threshold != float("inf"):
        kept = [value for value in values if abs(value - centre) <= threshold]
        dropped = len(values) - len(kept)
        if len(kept) < 2:  # never trim down to a single observation
            kept, dropped = list(values), 0
    return ReferenceStats(
        median=centre, low=min(kept), high=max(kept), used=len(kept), dropped=dropped
    )


def typical_band(stats: ReferenceStats, kind: str) -> tuple[float, float]:
    """The range we call normal, widened by a tolerance that fits the scale."""
    if kind == RATE:
        return max(0.0, stats.low - RATE_TOLERANCE), min(100.0, stats.high + RATE_TOLERANCE)
    slack = max(VOLUME_TOLERANCE, round(stats.median * VOLUME_RELATIVE_TOLERANCE))
    return max(0.0, stats.low - slack), stats.high + slack


def classify(
    current: float | None, stats: ReferenceStats | None, kind: str
) -> str:
    if stats is None or stats.used < MIN_REFERENCE_WEEKS:
        return INSUFFICIENT
    if current is None:
        return NOT_ENOUGH
    low, high = typical_band(stats, kind)
    if current > high:
        return ABOVE
    if current < low:
        return BELOW
    return WITHIN


@dataclass(frozen=True)
class SeriesPoint:
    week_start: date
    value: float
    current: bool


@dataclass(frozen=True)
class MetricResult:
    key: str
    label: str
    unit: str
    kind: str
    status: str
    current: float | None
    typical: float | None
    low: float | None
    high: float | None
    delta: float | None
    ratio: float | None
    numerator: int
    denominator: int | None
    series: tuple[SeriesPoint, ...]
    note: str | None = None
    #: Reference weeks that survived validation (internal, not serialised).
    references_used: int = 0
    #: Reference weeks excluded as outliers before computing the normal range.
    references_dropped: int = 0

    @property
    def deviates(self) -> bool:
        return self.status in (ABOVE, BELOW)


DayTallies = dict[date, dict[str, "Tally"]]


def tally_window(series: DayTallies, window: Window, location: str | None = None) -> Tally:
    """Sum the tallies inside a window, optionally for a single location."""
    tallies: list[Tally] = []
    for day in window.days():
        by_location = series.get(day)
        if not by_location:
            continue
        if location is None:
            tallies.extend(by_location.values())
        elif location in by_location:
            tallies.append(by_location[location])
    return sum_tallies(tallies)


def _shape(spec: MetricSpec, value: float | None) -> int | float | None:
    """Volumes stay integers on the wire; rates keep one decimal."""
    if value is None:
        return None
    return float(value) if spec.kind == RATE else int(round(value))


def _current_numerator(spec: MetricSpec, tally: Tally) -> int:
    return int(spec.numerator(tally))


def evaluate_metric(
    spec: MetricSpec,
    series: DayTallies,
    window: Window,
    references: Sequence[Window],
    location: str | None = None,
    note: str | None = None,
) -> MetricResult:
    current_tally = tally_window(series, window, location)
    current = _shape(spec, spec.value(current_tally))

    reference_values: list[float] = []
    points: list[SeriesPoint] = []
    # `references` is newest-first; the wire format reads oldest-first so the
    # sparkline can end on the current window.
    for reference in reversed(references):
        value = _shape(spec, spec.value(tally_window(series, reference, location)))
        if value is None:
            continue  # a rate with an unusable denominator contributes nothing
        reference_values.append(value)
        points.append(SeriesPoint(week_start=reference.start, value=value, current=False))

    stats = summarize_references(reference_values)
    status = classify(current, stats, spec.kind)

    typical = low = high = delta = ratio = None
    if stats is not None and status != INSUFFICIENT:
        band_low, band_high = typical_band(stats, spec.kind)
        typical = _shape(spec, stats.median)
        low = _shape(spec, band_low)
        high = _shape(spec, band_high)
        if current is not None:
            delta = _shape(spec, current - stats.median)
            ratio = round(current / stats.median, 2) if stats.median > 0 else None

    if current is not None:
        points.append(SeriesPoint(week_start=window.start, value=current, current=True))

    denominator = (
        int(spec.denominator(current_tally)) if spec.denominator is not None else None
    )
    return MetricResult(
        references_used=stats.used if stats is not None else 0,
        references_dropped=stats.dropped if stats is not None else 0,
        key=spec.key,
        label=spec.label,
        unit=spec.unit,
        kind=spec.kind,
        status=status,
        current=current,
        typical=typical,
        low=low,
        high=high,
        delta=delta,
        ratio=ratio,
        numerator=_current_numerator(spec, current_tally),
        denominator=denominator,
        series=tuple(points),
        note=note,
    )


def evaluate_all(
    series: DayTallies,
    window: Window,
    references: Sequence[Window],
    location: str | None = None,
) -> tuple[MetricResult, ...]:
    return tuple(
        evaluate_metric(spec, series, window, references, location) for spec in METRICS
    )


def with_note(result: MetricResult, note: str | None) -> MetricResult:
    return replace(result, note=note)
