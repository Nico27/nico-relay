#!/usr/bin/env bash
# End-to-end verification for DASH-247.
#
#   ./scripts/verify.sh
#
# Brings the local stack up, checks the seed, the API contract, the June-3 detection,
# that the API runs as uid 10001, and that the Vite dev server proxies to it.
# Fails fast on the first broken expectation. Requires docker, uv, node/npm, curl, python3.
set -euo pipefail

cd "$(dirname "$0")/.."

API_PORT="${API_HOST_PORT:-8010}"
WEB_PORT="${WEB_HOST_PORT:-5180}"

step() { printf '\n\033[1m▶ %s\033[0m\n' "$1"; }
ok() { printf '  ✓ %s\n' "$1"; }
fail() {
    printf '  ✗ %s\n' "$1" >&2
    exit 1
}

wait_for() {
    for _ in $(seq 1 90); do
        curl -sf "$1" >/dev/null 2>&1 && return 0
        sleep 2
    done
    return 1
}

json() { python3 -c "import json,sys; print($1)"; }

step "backend: static tests (no database)"
(cd backend && uv run pytest -q)

step "dev stack: db + api"
docker compose up -d --build db api >/dev/null
wait_for "http://localhost:${API_PORT}/healthz" || fail "api never became healthy"
ok "healthz"
[[ "$(curl -s "http://localhost:${API_PORT}/readyz" | json "json.load(sys.stdin)['database']")" == "ok" ]] \
    || fail "readyz does not report a healthy database"
ok "readyz reports the database"

step "seed invariants"
curl -s "http://localhost:${API_PORT}/api/v1/accounts" >/tmp/relay-accounts.json
[[ "$(json "len(json.load(open('/tmp/relay-accounts.json'))['accounts'])" < /tmp/relay-accounts.json)" == "20" ]] \
    || fail "expected 20 seeded accounts"
ok "20 accounts"
[[ "$(json "json.load(open('/tmp/relay-accounts.json'))['data_through']" < /tmp/relay-accounts.json)" == "2026-07-27" ]] \
    || fail "expected data_through 2026-07-27"
ok "data_through = 2026-07-27"

step "api contract"
curl -s "http://localhost:${API_PORT}/api/v1/accounts/6/dashboard" >/tmp/relay-dashboard.json
python3 - <<'PY'
import json

payload = json.load(open("/tmp/relay-dashboard.json"))
expected = {
    "account", "generated_at", "data_through", "as_of_source", "staleness_days", "empty",
    "period", "headline", "metrics", "in_progress", "locations", "drivers", "narrative",
    "data_quality",
}
assert set(payload) == expected, f"payload keys drifted: {set(payload) ^ expected}"
assert [m["key"] for m in payload["metrics"]] == [
    "activity", "calls", "missed_call_rate", "leads", "appointments", "no_show_rate",
], "metric order drifted"
assert payload["period"]["end"] < payload["data_through"], "period must be a complete week"
assert payload["locations"] and len(payload["locations"]) == 15, "expected 15 locations"
assert payload["headline"]["basis"] in ("last_week", "this_week"), "missing headline basis"
series = payload["metrics"][0]["series"]
assert series[-1]["current"] is True, "series must end with the current window"
assert series == sorted(series, key=lambda p: p["week_start"]), "series must be chronological"
for metric in payload["metrics"]:
    if metric["low"] is not None:
        assert metric["low"] <= metric["high"], metric["key"]
print("  ✓ payload shape, metric order, complete week, series order")
PY
[[ "$(curl -s -o /dev/null -w '%{http_code}' "http://localhost:${API_PORT}/api/v1/accounts/999/dashboard")" == "404" ]] \
    || fail "unknown account must be a 404"
ok "unknown account → 404"
[[ "$(curl -s -o /dev/null -w '%{http_code}' "http://localhost:${API_PORT}/api/v1/accounts/1/dashboard?baseline_weeks=0")" == "422" ]] \
    || fail "baseline_weeks=0 must be rejected"
ok "invalid baseline_weeks → 422"

step "the June 3 incident is visible"
curl -s "http://localhost:${API_PORT}/api/v1/accounts/6/dashboard?as_of=2026-06-08" >/tmp/relay-june.json
[[ "$(json "json.load(open('/tmp/relay-june.json'))['headline']['status']" < /tmp/relay-june.json)" == "above_typical" ]] \
    || fail "the June 3 spike was not detected"
[[ "$(json "len(json.load(open('/tmp/relay-june.json'))['drivers'])" < /tmp/relay-june.json)" -ge 1 ]] \
    || fail "the spike has no named drivers"
ok "above_typical with named drivers"

step "running as non-root"
UID_IN_CONTAINER="$(docker compose exec -T api id -u | tr -d '\r')"
[[ "$UID_IN_CONTAINER" == "10001" ]] || fail "api runs as uid ${UID_IN_CONTAINER}"
ok "api uid 10001"

step "frontend: typecheck + tests"
(cd frontend && npm run typecheck && npm test)

step "dev web server proxies to the api"
docker compose up -d web >/dev/null
wait_for "http://localhost:${WEB_PORT}/" || fail "vite dev server never answered"
ok "vite serves the app"
curl -s "http://localhost:${WEB_PORT}/api/v1/accounts" >/tmp/relay-proxy.json
[[ "$(json "len(json.load(open('/tmp/relay-proxy.json'))['accounts'])" < /tmp/relay-proxy.json)" == "20" ]] \
    || fail "the vite proxy did not reach the api"
ok "proxy /api -> api:8000"
WEB_UID="$(docker compose exec -T web id -u | tr -d '\r')"
printf '  · web container uid: %s (dev only)\n' "$WEB_UID"

printf '\n\033[32mAll checks passed.\033[0m\n'
