"""The sentence at the top of the dashboard.

Numbers and verdicts are computed by `stats.py` and never by this module. That
separation is the point: an LLM (or a human editor) can replace `Narrator` without
being able to change what the customer is told is normal — see PLAN.md, S9.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Protocol

from .stats import ABOVE, BELOW, INSUFFICIENT, WITHIN, MetricResult


def format_number(value: float | None) -> str:
    if value is None:
        return "—"
    if float(value).is_integer():
        return f"{int(value):,}"
    return f"{value:,.1f}"


def format_range(metric: MetricResult) -> str:
    if metric.low is None or metric.high is None:
        return "—"
    if metric.unit == "percent":
        return f"{metric.low:.1f}–{metric.high:.1f}%"
    return f"{format_number(metric.low)}–{format_number(metric.high)}"


def format_value(metric: MetricResult) -> str:
    if metric.current is None:
        return "—"
    if metric.unit == "percent":
        return f"{metric.current:.1f}%"
    return format_number(metric.current)


@dataclass(frozen=True)
class NarrativeDriver:
    location: str
    delta: float


@dataclass(frozen=True)
class NarrativeContext:
    account_name: str
    period_label: str
    headline_status: str
    metrics: Sequence[MetricResult]
    drivers: Sequence[NarrativeDriver]
    location_count: int
    empty: bool
    headline_basis: str = "last_week"


class Narrator(Protocol):
    """One method, so an LLM adapter can drop in behind the same interface."""

    def explain(self, context: NarrativeContext) -> str: ...


_OPENING = {
    ("last_week", ABOVE): "Last week was busier than usual",
    ("last_week", BELOW): "Last week was quieter than usual",
    ("last_week", WITHIN): "Last week looked normal",
    ("last_week", INSUFFICIENT): "There isn't enough history to judge yet",
    ("this_week", ABOVE): "This week is busier than usual so far",
    ("this_week", BELOW): "This week is quieter than usual so far",
    ("this_week", WITHIN): "This week looks normal so far",
}


def describe_multiple(ratio: float) -> str:
    """A multiplier a human can read, without implying precision we do not have."""
    if ratio >= 10:
        return f"about {round(ratio):,}× a normal week"
    return f"about {ratio:.1f}× a normal week"


class TemplateNarrator:
    """Deterministic, offline, and tested. Never invents a number."""

    def explain(self, context: NarrativeContext) -> str:
        if context.empty:
            return (
                f"We haven't received any activity from {context.account_name} yet. "
                "Once events arrive, this page will show whether a week is typical "
                "for you."
            )

        activity = next((m for m in context.metrics if m.key == "activity"), None)
        sentences: list[str] = []

        opening = _OPENING.get((context.headline_basis, context.headline_status))
        if opening and activity is not None and activity.current is not None:
            sentences.append(
                f"{opening}: "
                f"{self._activity_phrase(activity, basis=context.headline_basis)}."
            )
        elif opening:
            sentences.append(f"{opening}.")

        sentences.extend(self._deviation_sentences(context.metrics, skip="activity"))

        if context.drivers:
            sentences.append(self._drivers_sentence(context.drivers))

        if len(sentences) == 1 and context.headline_status == WITHIN:
            sentences.append(
                "Every other measure stayed inside its usual range."
            )

        if (
            context.location_count > 1
            and not context.drivers
            and context.headline_basis == "last_week"
        ):
            sentences.append(
                f"All {context.location_count} locations stayed inside their own usual range."
            )

        return " ".join(sentences)

    def _activity_phrase(self, activity: MetricResult, *, basis: str) -> str:
        value = format_value(activity)
        if activity.typical is None:
            return f"{value} in total"
        if basis == "this_week":
            return f"{value} so far"
        band = format_range(activity)
        phrase = f"{value} against a usual {band}"
        if activity.ratio is not None and activity.status in (ABOVE, BELOW):
            phrase = f"{value} against a usual {band} — {describe_multiple(activity.ratio)}"
        return phrase

    def _deviation_sentences(
        self, metrics: Sequence[MetricResult], skip: str
    ) -> list[str]:
        sentences: list[str] = []
        for metric in metrics:
            if metric.key == skip or not metric.deviates:
                continue
            if metric.current is None or metric.low is None or metric.high is None:
                continue
            direction = "higher" if metric.status == ABOVE else "lower"
            sentences.append(
                f"{metric.label} was {direction} than usual at {format_value(metric)} "
                f"(usually {format_range(metric)})."
            )
        return sentences

    def _drivers_sentence(self, drivers: Sequence[NarrativeDriver]) -> str:
        parts = []
        for driver in drivers:
            sign = "+" if driver.delta > 0 else "−"
            parts.append(f"{driver.location} ({sign}{format_number(abs(driver.delta))})")
        if len(parts) == 1:
            return f"Almost all of the change came from {parts[0]}."
        if len(parts) == 2:
            return f"Most of the change came from {parts[0]} and {parts[1]}."
        return (
            f"Most of the change came from {parts[0]}, {parts[1]} "
            f"and {parts[2]}."
        )
