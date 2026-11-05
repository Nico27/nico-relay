"""Composition: windows, drivers, coverage, notes, edge cases."""

from __future__ import annotations

from datetime import date, timedelta

import pytest
from conftest import ANCHOR, TODAY, FakeRepository, account, make_service, week_rows

from relay import stats
from relay.service import AccountNotFound, DashboardService, DataUnavailable, DayRow
from relay.stats import Tally


def multi_location_rows(
    *,
    anchor: date = ANCHOR,
    per_day: int = 5,
    spike: dict[tuple[date, str], int] | None = None,
    calls: int = 2,
    calls_with_outcome: int | None = None,
    missed: int = 0,
    locations=("Site A", "Site B", "Site C"),
):
    spike = spike or {}
    rows = []
    start = anchor - timedelta(days=63)
    for location in locations:
        day = start
        while day <= anchor:
            activity = spike.get((day, location), per_day)
            rows.append(
                (
                    day,
                    location,
                    Tally(
                        activity=activity,
                        calls=calls,
                        calls_with_outcome=(
                            calls if calls_with_outcome is None else calls_with_outcome
                        ),
                        missed=missed,
                    ),
                )
            )
            day += timedelta(days=1)
    return [DayRow(day=day, location=location, tally=tally) for day, location, tally in rows]


def service_for(rows, **account_kwargs) -> DashboardService:
    account_kwargs.setdefault(
        "locations", tuple(sorted({row.location for row in rows}))
    )
    entity = account(**account_kwargs)
    return make_service(FakeRepository(rows=rows, accounts=[entity]))


def test_a_spike_week_produces_a_headline_drivers_and_a_sentence() -> None:
    rows = multi_location_rows(
        spike={(date(2026, 7, 22), "Site C"): 300}
    )
    dashboard = service_for(rows).dashboard(6)

    assert dashboard.headline.status == stats.ABOVE
    assert dashboard.headline.metric_key == "activity"
    assert dashboard.metrics[0].key == "activity"
    assert dashboard.drivers
    assert dashboard.drivers[0].location == "Site C"
    assert dashboard.drivers[0].direction == "up"
    assert dashboard.drivers[0].delta > 0
    assert "busier than usual" in dashboard.narrative
    assert "Site C" in dashboard.narrative
    assert dashboard.locations[0].location == "Site C"
    assert sum(driver.share for driver in dashboard.drivers) <= 1.0


def test_period_is_a_complete_monday_to_sunday_week() -> None:
    dashboard = service_for(multi_location_rows()).dashboard(6)
    assert dashboard.period.start.weekday() == 0
    assert (dashboard.period.end - dashboard.period.start).days == 6
    assert dashboard.period.end == date(2026, 7, 26)
    assert dashboard.period.reference_weeks_used == 8
    assert dashboard.period.reference_weeks_skipped == 0


def test_this_week_so_far_is_compared_on_matching_weekdays() -> None:
    dashboard = service_for(multi_location_rows()).dashboard(6)
    assert dashboard.in_progress is not None
    assert dashboard.in_progress.start == date(2026, 7, 27)
    assert dashboard.in_progress.end == ANCHOR
    assert dashboard.in_progress.day_count == 1
    assert dashboard.in_progress.partial is True
    assert "1 day" in dashboard.in_progress.label
    # A one-day window must be measured against one-day references.
    activity = dashboard.in_progress.metrics[0]
    assert activity.typical == 15  # 3 locations x 5 events on a single Monday


def test_stale_data_is_disclosed_rather_than_implied() -> None:
    dashboard = service_for(multi_location_rows()).dashboard(6)
    assert dashboard.data_through == ANCHOR
    assert dashboard.staleness_days == (TODAY - ANCHOR).days == 101
    codes = [note.code for note in dashboard.data_quality]
    assert "stale_data" in codes
    stale = next(note for note in dashboard.data_quality if note.code == "stale_data")
    assert stale.severity == "warning"
    assert "Jul 27" in stale.message


def test_calls_without_outcomes_are_excluded_and_disclosed() -> None:
    rows = multi_location_rows(calls=4, calls_with_outcome=3, missed=1)
    dashboard = service_for(rows).dashboard(6)
    missed = next(m for m in dashboard.metrics if m.key == "missed_call_rate")
    assert missed.denominator == 3 * 3 * 7  # locations x calls with an outcome x days
    assert missed.current == pytest.approx(100 * (1 * 3 * 7) / (3 * 3 * 7), abs=0.1)
    assert missed.note is not None and "no outcome" in missed.note
    assert "outcome_gaps" in [note.code for note in dashboard.data_quality]


def test_an_account_with_no_events_gets_an_empty_state_not_a_verdict() -> None:
    entity = account(
        event_count=0, first_event_local=None, last_event_local=None, locations=()
    )
    dashboard = make_service(FakeRepository(rows=[], accounts=[entity])).dashboard(6)
    assert dashboard.empty is True
    assert dashboard.headline.status == stats.NO_ACTIVITY
    assert dashboard.headline.basis is None
    assert dashboard.in_progress is not None
    assert all(
        metric.status == stats.INSUFFICIENT for metric in dashboard.in_progress.metrics
    )
    assert all(metric.status == stats.INSUFFICIENT for metric in dashboard.metrics)
    assert all(metric.current in (0, None) for metric in dashboard.metrics)
    assert dashboard.locations == []
    assert "haven't received any activity" in dashboard.narrative


def test_an_account_with_too_little_history_refuses_to_judge() -> None:
    entity = account(created_local=date(2026, 7, 1), first_event_local=date(2026, 7, 1))
    rows = week_rows(ANCHOR, weeks=3, per_day=10)
    dashboard = make_service(FakeRepository(rows=rows, accounts=[entity])).dashboard(6)
    activity = dashboard.metrics[0]
    assert activity.status == stats.INSUFFICIENT
    assert activity.typical is None
    assert activity.low is None
    assert dashboard.headline.title == "Not enough history to tell yet"
    codes = [note.code for note in dashboard.data_quality]
    assert "reference_weeks_skipped" in codes


def test_as_of_is_honoured_and_clamped() -> None:
    service = service_for(multi_location_rows())
    requested = service.dashboard(6, as_of=date(2026, 7, 20))
    assert requested.as_of_source == "requested"
    assert requested.data_through == date(2026, 7, 20)
    assert requested.period.end == date(2026, 7, 19)

    future = service.dashboard(6, as_of=date(2027, 1, 1))
    assert future.data_through == ANCHOR
    assert future.as_of_source == "requested"


def test_baseline_weeks_are_configurable() -> None:
    dashboard = service_for(multi_location_rows()).dashboard(6, baseline_weeks=4)
    assert dashboard.period.baseline_weeks == 4
    assert dashboard.period.reference_weeks_used == 4


def test_unknown_account_and_missing_data_are_distinct_errors() -> None:
    service = service_for(multi_location_rows())
    with pytest.raises(AccountNotFound):
        service.dashboard(999)
    empty_repository = FakeRepository(rows=[], accounts=[account()], data_through=None)
    with pytest.raises(DataUnavailable):
        make_service(empty_repository).dashboard(6)


def test_a_location_that_went_silent_is_called_out() -> None:
    rows = multi_location_rows()
    silent_day_from = date(2026, 7, 20)
    rows = [
        row
        for row in rows
        if not (row.location == "Site B" and row.day >= silent_day_from)
    ]
    dashboard = service_for(rows).dashboard(6)
    site_b = next(row for row in dashboard.locations if row.location == "Site B")
    assert site_b.current == 0
    assert site_b.status == stats.BELOW
    assert site_b.note == "No activity in this period."
    assert "location_silent" in [note.code for note in dashboard.data_quality]


def test_roster_carries_locations_and_freshness() -> None:
    entity = account(locations=("Site A", "Site B"))
    roster = make_service(FakeRepository(rows=[], accounts=[entity])).list_accounts()
    assert roster.data_through == ANCHOR
    assert roster.accounts[0].locations == ["Site A", "Site B"]
    assert roster.accounts[0].last_event_at is not None


def test_payload_is_json_serialisable_with_sorted_locations() -> None:
    dashboard = service_for(
        multi_location_rows(spike={(date(2026, 7, 21), "Site B"): 90})
    ).dashboard(6)
    payload = dashboard.model_dump(mode="json")
    import json

    text = json.dumps(payload)
    assert '"status": "above_typical"' in text
    deltas = [abs(row["delta"] or 0) for row in payload["locations"]]
    assert deltas == sorted(deltas, reverse=True)


def test_a_thursday_spike_leads_with_this_week_not_last_week() -> None:
    # Data through Thursday Jul 30: the open week already shows the anomaly.
    anchor = date(2026, 7, 30)
    rows = multi_location_rows(
        anchor=anchor,
        spike={(date(2026, 7, 28), "Site B"): 200, (date(2026, 7, 29), "Site B"): 200},
    )
    repository = FakeRepository(
        rows=rows,
        accounts=[account(locations=("Site A", "Site B", "Site C"))],
        data_through=anchor,
    )
    dashboard = make_service(repository).dashboard(6)

    assert dashboard.period.end == date(2026, 7, 26)  # the stable week is still reported
    assert dashboard.metrics[0].status == stats.WITHIN
    assert dashboard.headline.basis == "this_week"
    assert dashboard.headline.status == stats.ABOVE
    assert dashboard.headline.title == "This week is busier than usual so far"
    assert "so far" in dashboard.headline.detail
    assert dashboard.drivers and dashboard.drivers[0].location == "Site B"
    assert "This week is busier than usual so far" in dashboard.narrative
    assert dashboard.in_progress is not None
    assert dashboard.in_progress.day_count == 4


def test_a_single_day_of_data_never_leads_the_headline() -> None:
    anchor = date(2026, 7, 27)  # Monday: the open week is one day old
    rows = multi_location_rows(anchor=anchor, spike={(anchor, "Site C"): 400})
    repository = FakeRepository(rows=rows, accounts=[account()], data_through=anchor)
    dashboard = make_service(repository).dashboard(6)

    assert dashboard.headline.basis == "last_week"
    assert dashboard.headline.status == stats.WITHIN


def test_the_narrator_is_replaceable_seam() -> None:
    """S9: an LLM may write the prose, but it must not write the numbers."""

    class RecordingNarrator:
        def __init__(self) -> None:
            self.contexts = []

        def explain(self, context) -> str:
            self.contexts.append(context)
            return "llm-style prose"

    narrator = RecordingNarrator()
    entity = account(locations=("Site A",))
    service = make_service(
        FakeRepository(rows=multi_location_rows(locations=("Site A",)), accounts=[entity]),
        narrator=narrator,
    )
    dashboard = service.dashboard(6)

    assert dashboard.narrative == "llm-style prose"
    assert len(narrator.contexts) == 1
    context = narrator.contexts[0]
    assert context.headline_status == dashboard.headline.status
    # The seam receives computed verdicts; it cannot change what "normal" means.
    assert all(metric.status for metric in context.metrics)
    assert context.metrics[0].current == dashboard.metrics[0].current


def test_an_outlier_reference_week_is_excluded_and_disclosed() -> None:
    """One freak week must not define normal for the next two months."""
    rows = multi_location_rows(spike={(date(2026, 6, 3), "Site C"): 400})
    dashboard = service_for(rows).dashboard(6)

    assert dashboard.period.reference_weeks_used == 7
    codes = [note.code for note in dashboard.data_quality]
    assert "reference_weeks_excluded" in codes
    note = next(n for n in dashboard.data_quality if n.code == "reference_weeks_excluded")
    assert "left out of your normal range" in note.message
    # The excluded week is still plotted: the customer can see it happened.
    activity = dashboard.metrics[0]
    assert len([point for point in activity.series if not point.current]) == 8
    assert max(point.value for point in activity.series) > 100
