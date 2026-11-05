"""HTTP surface. No database: the service is injected."""

from __future__ import annotations

from conftest import ANCHOR, FakeRepository, account, make_service, week_rows
from fastapi.testclient import TestClient

from relay.main import create_app

CONTRACT_KEYS = {
    "account",
    "generated_at",
    "data_through",
    "as_of_source",
    "staleness_days",
    "empty",
    "period",
    "headline",
    "metrics",
    "in_progress",
    "locations",
    "drivers",
    "narrative",
    "data_quality",
}

METRIC_KEYS = {
    "key",
    "label",
    "unit",
    "kind",
    "status",
    "current",
    "typical",
    "low",
    "high",
    "delta",
    "ratio",
    "numerator",
    "denominator",
    "series",
    "note",
}


def client(rows=None, accounts=None) -> TestClient:
    repository = FakeRepository(
        rows=week_rows(ANCHOR, weeks=9, per_day=10) if rows is None else rows,
        accounts=[account()] if accounts is None else accounts,
    )
    return TestClient(create_app(service=make_service(repository)))


def test_health_is_dependency_free() -> None:
    response = client().get("/healthz")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_readiness_reports_not_checked_without_a_pool() -> None:
    response = client().get("/readyz")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_accounts_endpoint_lists_the_roster() -> None:
    response = client().get("/api/v1/accounts")
    assert response.status_code == 200
    body = response.json()
    assert body["data_through"] == ANCHOR.isoformat()
    assert body["accounts"][0]["id"] == 6
    assert body["accounts"][0]["locations"] == ["Site A"]


def test_dashboard_matches_the_contract() -> None:
    response = client().get("/api/v1/accounts/6/dashboard")
    assert response.status_code == 200
    body = response.json()
    assert set(body) == CONTRACT_KEYS
    assert [metric["key"] for metric in body["metrics"]] == [
        "activity",
        "calls",
        "missed_call_rate",
        "leads",
        "appointments",
        "no_show_rate",
    ]
    assert all(set(metric) == METRIC_KEYS for metric in body["metrics"])
    assert body["period"]["start"] == "2026-07-20"
    assert body["period"]["end"] == "2026-07-26"
    assert body["headline"]["status"] == "within_typical"
    assert body["account"] == {
        "id": 6,
        "name": "Metro Collision Centers",
        "industry": "Automotive Services",
        "timezone": "America/Chicago",
    }
    assert body["in_progress"]["day_count"] == 1


def test_unknown_account_is_a_404() -> None:
    response = client().get("/api/v1/accounts/999/dashboard")
    assert response.status_code == 404
    assert response.json() == {"detail": "Account not found"}


def test_invalid_baseline_window_is_rejected() -> None:
    assert client().get("/api/v1/accounts/6/dashboard?baseline_weeks=0").status_code == 422
    assert client().get("/api/v1/accounts/6/dashboard?baseline_weeks=27").status_code == 422
    assert client().get("/api/v1/accounts/6/dashboard?as_of=not-a-date").status_code == 422


def test_as_of_parameter_changes_the_horizon() -> None:
    body = client().get("/api/v1/accounts/6/dashboard?as_of=2026-07-20").json()
    assert body["as_of_source"] == "requested"
    assert body["data_through"] == "2026-07-20"
    assert body["period"]["end"] == "2026-07-19"


def test_empty_account_returns_a_usable_payload() -> None:
    empty = account(event_count=0, first_event_local=None, last_event_local=None, locations=())
    body = client(rows=[], accounts=[empty]).get("/api/v1/accounts/6/dashboard").json()
    assert body["empty"] is True
    assert body["headline"]["status"] == "no_activity"
    assert body["locations"] == []
    assert isinstance(body["narrative"], str) and body["narrative"]


def test_no_data_at_all_is_a_503() -> None:
    repository = FakeRepository(rows=[], accounts=[account()], data_through=None)
    response = TestClient(create_app(service=make_service(repository))).get(
        "/api/v1/accounts/6/dashboard"
    )
    assert response.status_code == 503
