"""The judgement, without a database."""

from __future__ import annotations

from datetime import date, timedelta

import pytest
from conftest import ANCHOR, days, flat_rows, week_rows

from relay import stats
from relay.stats import Tally


class TestCalendar:
    @pytest.mark.parametrize(
        ("anchor", "week_start", "week_end"),
        [
            (date(2026, 7, 27), date(2026, 7, 20), date(2026, 7, 26)),  # Monday
            (date(2026, 7, 28), date(2026, 7, 20), date(2026, 7, 26)),  # Tuesday
            (date(2026, 8, 2), date(2026, 7, 20), date(2026, 7, 26)),  # Sunday
        ],
    )
    def test_complete_week_never_uses_a_partial_week(
        self, anchor: date, week_start: date, week_end: date
    ) -> None:
        window = stats.previous_complete_week(stats.last_complete_day(anchor))
        assert window == stats.Window(week_start, week_end)
        assert window.day_count == 7

    def test_partial_window_holds_the_days_after_the_judged_week(self) -> None:
        primary = stats.Window(date(2026, 7, 20), date(2026, 7, 26))
        partial = stats.partial_window(primary, date(2026, 7, 29))
        assert partial == stats.Window(date(2026, 7, 27), date(2026, 7, 29))
        assert partial.day_count == 3

    def test_partial_window_is_none_when_the_week_is_current(self) -> None:
        primary = stats.Window(date(2026, 7, 20), date(2026, 7, 26))
        assert stats.partial_window(primary, date(2026, 7, 26)) is None

    def test_reference_windows_match_weekdays_and_skip_early_history(self) -> None:
        window = stats.Window(date(2026, 7, 20), date(2026, 7, 26))
        references, skipped = stats.reference_windows(
            window, 8, history_start=date(2026, 6, 15)
        )
        assert skipped == 3  # three weeks start before 2026-06-15
        assert references[0] == stats.Window(date(2026, 7, 13), date(2026, 7, 19))
        assert all(reference.start.weekday() == 0 for reference in references)
        assert len(references) + skipped == 8

    def test_partial_window_references_keep_the_short_shape(self) -> None:
        window = stats.Window(date(2026, 7, 27), date(2026, 7, 29))  # Mon–Wed
        references, _ = stats.reference_windows(window, 4, history_start=date(2026, 1, 1))
        assert [reference.day_count for reference in references] == [3, 3, 3, 3]
        assert references[0] == stats.Window(date(2026, 7, 20), date(2026, 7, 22))


class TestSummarize:
    def test_median_of_even_and_odd_counts(self) -> None:
        assert stats.median([3, 1, 2]) == 2
        assert stats.median([4, 1, 3, 2]) == 2.5

    def test_one_freak_week_is_trimmed_not_absorbed(self) -> None:
        # A week at 800 events among eight weeks of ~70 must not widen "normal".
        result = stats.summarize_references([70, 72, 68, 71, 800, 69, 73, 70])
        assert result is not None
        assert result.dropped == 1
        assert result.median == 70.5
        assert result.high == 73
        assert result.low == 68

    def test_flat_history_gets_a_scale_aware_cushion(self) -> None:
        result = stats.summarize_references([70, 70, 70, 70])
        assert result is not None
        assert (result.low, result.high) == (70, 70)
        low, high = stats.typical_band(result, stats.VOLUME)
        assert (low, high) == (63, 77)  # 10% of the median, never a point band

    def test_trim_never_leaves_a_single_observation(self) -> None:
        # Two kept values is still an observation pair; one would not be.
        result = stats.summarize_references([10, 11, 900])
        assert result is not None
        assert result.used == 2
        assert result.dropped == 1


class TestClassify:
    def test_refuses_to_judge_with_three_reference_weeks(self) -> None:
        result = stats.summarize_references([70, 70, 70])
        assert result is not None
        assert stats.classify(500, result, stats.VOLUME) == stats.INSUFFICIENT

    @pytest.mark.parametrize(
        ("current", "expected"),
        [
            (72, stats.WITHIN),
            (77, stats.WITHIN),
            (63, stats.WITHIN),
            (78, stats.ABOVE),
            (62, stats.BELOW),
        ],
    )
    def test_volume_bands_include_the_scale_aware_tolerance(self, current, expected) -> None:
        result = stats.summarize_references([70, 70, 70, 70])
        assert stats.classify(current, result, stats.VOLUME) == expected

    def test_rates_get_a_percentage_point_floor(self) -> None:
        result = stats.summarize_references([10.0, 10.4, 9.8, 10.2, 9.9])
        assert stats.classify(11.2, result, stats.RATE) == stats.WITHIN
        assert stats.classify(11.6, result, stats.RATE) == stats.ABOVE

    def test_rate_above_one_hundred_percent_is_capped(self) -> None:
        result = stats.summarize_references([99.0, 99.5])
        low, high = stats.typical_band(result, stats.RATE)
        assert (low, high) == (98.0, 100.0)


class TestEvaluateMetric:
    def test_volume_window_sums_per_week_not_per_day(self) -> None:
        rows = week_rows(ANCHOR, weeks=9, per_day=10)
        series = _series(rows)
        window = stats.Window(date(2026, 7, 20), date(2026, 7, 26))
        references, _ = stats.reference_windows(window, 8, history_start=date(2026, 1, 1))
        result = stats.evaluate_metric(
            stats.METRICS_BY_KEY["activity"], series, window, references
        )
        assert result.current == 70
        assert result.typical == 70
        assert result.status == stats.WITHIN
        assert len([point for point in result.series if not point.current]) == 8
        # Oldest first, current last: the sparkline reads left to right.
        assert result.series == tuple(sorted(result.series, key=lambda p: p.week_start))
        assert result.series[-1].current is True
        assert result.series[0].week_start == date(2026, 5, 25)

    def test_a_spike_is_above_and_its_ratio_is_meaningful(self) -> None:
        rows = week_rows(ANCHOR, weeks=9, per_day=10, override={date(2026, 7, 22): 300})
        series = _series(rows)
        window = stats.Window(date(2026, 7, 20), date(2026, 7, 26))
        references, _ = stats.reference_windows(window, 8, history_start=date(2026, 1, 1))
        result = stats.evaluate_metric(
            stats.METRICS_BY_KEY["activity"], series, window, references
        )
        assert result.current == 360
        assert result.status == stats.ABOVE
        assert result.ratio == pytest.approx(5.14, abs=0.01)

    def test_rate_metric_matches_on_the_ratio_of_counts(self) -> None:
        rows = week_rows(
            ANCHOR,
            weeks=9,
            per_day=10,
            calls=4,
            calls_with_outcome=4,
            missed=1,
        )
        series = _series(rows)
        window = stats.Window(date(2026, 7, 20), date(2026, 7, 26))
        references, _ = stats.reference_windows(window, 8, history_start=date(2026, 1, 1))
        result = stats.evaluate_metric(
            stats.METRICS_BY_KEY["missed_call_rate"], series, window, references
        )
        assert result.current == 25.0
        assert result.denominator == 28
        assert result.status == stats.WITHIN

    def test_rate_with_a_tiny_denominator_refuses_to_report(self) -> None:
        # Two calls in a week is not a missed-call rate, it is two calls.
        rows = flat_rows(
            date(2026, 7, 20),
            date(2026, 7, 21),
            tally=Tally(activity=1, calls=1, calls_with_outcome=1, missed=1),
        )
        series = _series(rows)
        window = stats.Window(date(2026, 7, 20), date(2026, 7, 26))
        result = stats.evaluate_metric(
            stats.METRICS_BY_KEY["missed_call_rate"], series, window, []
        )
        assert result.current is None
        assert result.denominator == 2
        assert result.status == stats.INSUFFICIENT

    def test_rate_with_enough_history_and_a_thin_window_still_refuses(self) -> None:
        rows = [
            row
            for row in week_rows(ANCHOR, weeks=9, per_day=1, calls=1, calls_with_outcome=1)
            if row.day < date(2026, 7, 20)
        ]
        rows += flat_rows(
            date(2026, 7, 20), date(2026, 7, 26), tally=Tally(activity=1, calls=0)
        )
        series = _series(rows)
        window = stats.Window(date(2026, 7, 20), date(2026, 7, 26))
        references, _ = stats.reference_windows(window, 8, history_start=date(2026, 1, 1))
        result = stats.evaluate_metric(
            stats.METRICS_BY_KEY["missed_call_rate"], series, window, references
        )
        assert result.current is None
        assert result.status == stats.NOT_ENOUGH

    def test_a_single_location_can_be_evaluated_on_its_own(self) -> None:
        rows = flat_rows(
            date(2026, 7, 20),
            date(2026, 7, 26),
            location="Site A",
            tally=Tally(activity=5),
        ) + flat_rows(
            date(2026, 7, 20),
            date(2026, 7, 26),
            location="Site B",
            tally=Tally(activity=50),
        )
        series = _series(rows)
        window = stats.Window(date(2026, 7, 20), date(2026, 7, 26))
        assert stats.tally_window(series, window, "Site A").activity == 35
        assert stats.tally_window(series, window).activity == 385


def _series(rows) -> stats.DayTallies:
    series: stats.DayTallies = {}
    for row in rows:
        series.setdefault(row.day, {})[row.location] = row.tally
    return series


def test_tally_addition_is_field_wise() -> None:
    left = Tally(activity=3, calls=2, calls_with_outcome=1, missed=1)
    right = Tally(activity=4, calls=3, calls_with_outcome=3, missed=2, no_shows=1)
    total = left + right
    assert total.activity == 7
    assert total.calls == 5
    assert total.calls_with_outcome == 4
    assert total.missed == 3
    assert total.no_shows == 1


def test_days_helper_matches_window_days() -> None:
    window = stats.Window(date(2026, 7, 20), date(2026, 7, 26))
    assert window.days() == tuple(days(window.start, window.end))
    assert (window.start + timedelta(days=0)).weekday() == 0
