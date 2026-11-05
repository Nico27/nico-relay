"""The sentence the customer reads. No numbers are invented here."""

from __future__ import annotations

from datetime import date

from relay import stats
from relay.narrative import (
    NarrativeContext,
    NarrativeDriver,
    TemplateNarrator,
    format_number,
    format_range,
    format_value,
)
from relay.stats import MetricResult, SeriesPoint

NARRATOR = TemplateNarrator()


def metric(key: str, *, current, typical, low, high, status, unit="events", ratio=None):
    return MetricResult(
        key=key,
        label=stats.METRICS_BY_KEY[key].label,
        unit=unit,
        kind=stats.METRICS_BY_KEY[key].kind,
        status=status,
        current=current,
        typical=typical,
        low=low,
        high=high,
        delta=None,
        ratio=ratio,
        numerator=int(current or 0),
        denominator=None,
        series=(SeriesPoint(date(2026, 7, 20), current or 0, True),),
    )


def context(headline, metrics, drivers=(), empty=False, location_count=2) -> NarrativeContext:
    return NarrativeContext(
        account_name="Metro Collision Centers",
        period_label="Jul 20 – Jul 26",
        headline_status=headline,
        metrics=metrics,
        drivers=drivers,
        location_count=location_count,
        empty=empty,
    )


def test_typical_week_says_so_and_confirms_the_rest() -> None:
    metrics = [
        metric("activity", current=253, typical=260, low=220, high=300, status=stats.WITHIN),
        metric("calls", current=98, typical=99, low=90, high=110, status=stats.WITHIN),
    ]
    text = NARRATOR.explain(context(stats.WITHIN, metrics))
    assert text.startswith("Last week looked normal: 253 against a usual 220–300.")
    assert "Every other measure stayed inside its usual range." in text


def test_high_week_names_the_ratio_and_the_drivers() -> None:
    metrics = [
        metric(
            "activity",
            current=805,
            typical=15,
            low=12,
            high=18,
            status=stats.ABOVE,
            ratio=53.67,
        ),
        metric(
            "missed_call_rate",
            current=14.4,
            typical=9.0,
            low=8.0,
            high=10.0,
            status=stats.ABOVE,
            unit="percent",
        ),
    ]
    text = NARRATOR.explain(
        context(
            stats.ABOVE,
            metrics,
            drivers=(
                NarrativeDriver("Site C", 62),
                NarrativeDriver("Site A", 48),
            ),
        )
    )
    assert "Last week was busier than usual" in text
    assert "about 54× a normal week" in text
    assert "Missed-call rate was higher than usual at 14.4% (usually 8.0–10.0%)." in text
    assert "Most of the change came from Site C (+62) and Site A (+48)." in text


def test_multipliers_are_readable_not_precise() -> None:
    from relay.narrative import describe_multiple

    assert describe_multiple(13.33) == "about 13× a normal week"
    assert describe_multiple(3.75) == "about 3.8× a normal week"
    assert describe_multiple(1.24) == "about 1.2× a normal week"


def test_three_drivers_are_all_named() -> None:
    metrics = [metric("activity", current=1, typical=1, low=1, high=1, status=stats.ABOVE)]
    text = NARRATOR.explain(
        context(
            stats.ABOVE,
            metrics,
            drivers=(
                NarrativeDriver("Site C", 62),
                NarrativeDriver("Site A", 48),
                NarrativeDriver("Site B", -7),
            ),
        )
    )
    assert "Site C (+62), Site A (+48) and Site B (−7)" in text


def test_insufficient_history_says_so_without_judging() -> None:
    metrics = [
        metric("activity", current=10, typical=None, low=None, high=None, status=stats.INSUFFICIENT)
    ]
    text = NARRATOR.explain(context(stats.INSUFFICIENT, metrics))
    assert "There isn't enough history to judge yet" in text
    assert "higher than usual" not in text
    assert "lower than usual" not in text


def test_empty_account_gets_an_explanation_not_a_zero() -> None:
    text = NARRATOR.explain(context(stats.NO_ACTIVITY, [], empty=True))
    assert "haven't received any activity from Metro Collision Centers yet" in text


def test_formatters_are_stable() -> None:
    assert format_number(1223) == "1,223"
    assert format_number(12.5) == "12.5"
    assert format_number(None) == "—"
    flat = metric(
        "activity", current=70, typical=70, low=69, high=71, status=stats.WITHIN
    )
    assert format_value(flat) == "70"
    assert (
        format_value(
            metric(
                "missed_call_rate",
                current=22.3,
                typical=13.0,
                low=12.0,
                high=15.0,
                status=stats.ABOVE,
                unit="percent",
            )
        )
        == "22.3%"
    )
    assert (
        format_range(
            metric(
                "missed_call_rate",
                current=22.3,
                typical=13.0,
                low=12.0,
                high=15.0,
                status=stats.ABOVE,
                unit="percent",
            )
        )
        == "12.0–15.0%"
    )
