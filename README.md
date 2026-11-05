# Relay — "is this normal for us?" (DASH-247)

A Monday-morning dashboard that answers one question: **is this week's activity normal for this
customer?** No exports, no account manager, no forecasting.

The ticket was intentionally light. What "normal", "recent" and "actionable" mean here is
decided and argued in [`PLAN.md`](./PLAN.md). The wire contract is
[`docs/api.md`](./docs/api.md), and real payloads are in
[`docs/sample-payloads.json`](./docs/sample-payloads.json).

## Quickstart

```bash
cp env.example .env          # optional; sensible defaults are built in
docker compose up --build    # db + api (hot reload) + web (vite dev)
```

* dashboard — <http://localhost:5180>
* API + OpenAPI — <http://localhost:8010/docs>
* Postgres — `localhost:55432` (`relay` / `relay`)

The API container runs the migrations on start and loads `seed.sql` when the database is
empty (`SEED_ON_START=1`).
Host ports are unusual on purpose: 5432, 8000 and 5173 are routinely taken by other local
stacks; override `DB_HOST_PORT`, `API_HOST_PORT`, `WEB_HOST_PORT` in `.env`.

## What the screen says

1. **A plain answer first**: "4 of 6 measures are unusual", then "Last week was busier than
   usual: 880 against a usual 46–93 — about 13× a normal week", then **Start here:** with the
   three sites to look at. No statistics vocabulary is required to read any of it.
2. **Six metric cards** — activity, calls, missed-call rate, leads, appointments, no-show rate —
   each with the current value, its usual range ("usually 46–93"), a bar chart labelled *8 weeks
   ago → now* with the usual range shaded, and a chip that says Higher / Lower / Normal.
3. **A location table** for multi-location accounts, sorted by how much each site contributed to
   the deviation. This is the difference between "the week is up" and "the week is up and it is
   Brentwood".
4. **This week so far**, compared against the same weekdays in prior weeks — never a 3-day
   window against a 7-day one.
5. **Data-quality notes**: stale data, calls with no outcome, silent locations, skipped
   reference weeks.

The headline describes the last complete week, and switches to the open week when that week has
at least two days of data and is already outside its own usual range. A Thursday should not be
told "last week was fine" while this week is on fire.

## Architecture

```
frontend/            React + TS + Vite. One page, no UI kit, no chart library.
  src/components/    Headline, MetricCard, Sparkline, LocationTable, WeekSoFar, …
  src/format.ts      All display formatting, pure and unit tested.
backend/
  src/relay/
    stats.py         The judgement: windows, reference weeks, robust range, verdicts. Pure.
    service.py       Composition: drivers, coverage, data-quality notes, headline basis.
    repository.py    One grouped SQL query per screen; day bucketing via AT TIME ZONE.
    narrative.py     The sentence. Numbers come from stats.py, never from here.
    seed.py          Parses/validates/normalises seed.sql, COPYs it in, reports what it changed.
    migrate.py       Forward-only SQL migration runner (schema_migrations).
    main.py          FastAPI: /healthz, /readyz, /api/v1/accounts, …/dashboard.
  migrations/        Plain SQL. 0001_init.sql is an adapted schema.sql.
  tests/             76 tests: pure logic, API with an injected service, SQL against Postgres.
docs/api.md          Contract, status enum, note codes.
PLAN.md              Product decisions and their reasoning.
odd/tasks/…          ODD working document: specs, tasks, evidence log.
```

The dependency direction is deliberate: `stats.py` knows nothing about SQL, HTTP or prose, which
is why the verdict logic has fast, deterministic tests and why the narrator can be swapped for an
LLM without touching the numbers.

## Data: migration and seed

`schema.sql` is ported to `backend/migrations/0001_init.sql` with three changes, each commented
in place: `timestamptz` instead of naive UTC timestamps, identity columns that accept the seed's
explicit ids, and a `CHECK` on `event_type` so an unknown type fails loudly instead of vanishing
from every metric.

`seed.sql` is a data export, not a fixture. The loader validates it and prints what it changed:

```
accounts loaded: 20
events loaded:   12614
exact duplicates dropped: 12
durations cleared on non-call events: 0
```

Findings it handles (details in `PLAN.md`):

| Finding | Handling |
| --- | --- |
| 12 byte-identical duplicate events | Dropped once at ingest, counted, no unique constraint added (two identical simultaneous events are legal) |
| 313 calls with NULL duration; missed/voicemail calls average ~740 s | Duration is used by **no** MVP metric — it is unreliable for non-connected calls |
| 398 events with NULL outcome | Excluded from rate denominators, gap disclosed on the dashboard |
| `Quiet Harbor Spa` has zero events | First-class empty state, never "0% below usual" |
| Data ends 2026-07-27 (101 days before today) | Anchor defaults to the newest data day, the UI says "Data through Jul 27" and flags the lag |

Run the data commands by hand:

```bash
cd backend
export DATABASE_URL=postgresql://relay:relay@localhost:55432/relay
uv run python -m relay.migrate
uv run python -m relay.seed --reset --seed ../seed.sql
uv run python -m relay.seed --dry-run --seed ../seed.sql   # validate only
```

## Tests

```bash
cd backend
uv run pytest -q                                  # 66 unit/API tests, no database needed
TEST_DATABASE_URL=postgresql://relay:relay@localhost:55432/relay uv run pytest -q
                                                   # + 10 SQL integration tests

cd ../frontend
npm run typecheck && npm test

./scripts/verify.sh    # the whole thing: stack up, seed, contract, June-3, uid, proxy
```

Inside the dev stack: `docker compose exec api uv run pytest -q`.

What is pinned and why:

* The verdict engine: calendar windows, weekday matching, outlier trimming, tolerance floor,
  minimum reference weeks, minimum rate denominators.
* The composition layer: headline basis, drivers, coverage notes, empty and thin-history cases.
* The HTTP contract: exact top-level keys, metric order and keys, 404/422/503 behaviour.
* The SQL: the June 3 incident (804 events over 15 locations after dedupe), outcome gaps, and
  that `02:00Z` on Jul 28 buckets to **Jul 27** in Los Angeles.
* The seed contract: 20 accounts, 12,614 events, 12 duplicates, and every hard error path.

## Docker

Two containers, both for local work:

* **`api`** — one image (`Dockerfile`), no build stage for the frontend, no static hosting.
  It runs as **uid 10001** (nothing in it needs root): `docker compose exec api id`.
* **`web`** — stock `node:22-alpine` running Vite; the only process that runs as root, because
  the `node` user cannot write the bind-mounted `node_modules` volume.
* **Hot reload on both sides.** `api` mounts `backend/src` and runs uvicorn `--reload`; `web`
  mounts `frontend/` and proxies `/api` to `http://api:8000` (`VITE_PROXY_TARGET`).
* **Migrations on start**, then an optional seed, then the process — all in
  `backend/entrypoint.sh`. Everything it does is idempotent, so restarts are safe.
* **Healthchecks**: Postgres `pg_isready` and the API image hits `/healthz`; `/readyz` checks
  the database.

## Configuration

| Variable | Default | Meaning |
| --- | --- | --- |
| `DATABASE_URL` | `postgresql://relay:relay@localhost:5432/relay` | Postgres DSN |
| `BASELINE_WEEKS` | `8` | Preceding weeks used as the baseline |
| `MIGRATIONS_DIR` | `backend/migrations` | Where the SQL migrations live |
| `SEED_ON_START` | `0` in the image, `1` in compose | `1` loads `seed.sql` only when the database is empty; `reset` truncates and reloads; anything else never touches the data |
| `TEST_DATABASE_URL` | unset | Enables the integration tests |

`SEED_ON_START=1` is restart-safe on purpose: restarting the stack must never wipe your
local data. Use `make seed` (which passes `--reset`) when you actually want a clean reload.

## Security notes

Local-development scope, deliberately: this does not ship anywhere, and the missing pieces
matter:

* **No authentication and no tenancy.** `/api/v1/accounts/{id}/dashboard` is an unauthenticated
  read. That is acceptable only for a single-customer deployment behind a private network. Before
  anything else ships: session auth, per-account authorization derived from the session (never
  from the URL), and a tenant column enforced in every query.
* **No write endpoints.** The API is read-only; data arrives from ingest. There is no path from
  HTTP to a mutation, which also means no request-body validation to get wrong.
* **No secrets in the image.** Only `DATABASE_URL` and `BASELINE_WEEKS` are read, from the
  environment; the container runs as a non-root user.
* **No PII beyond business metrics.** Accounts, locations and event counts. No customer names,
  phone numbers or call content is stored or returned. `location` is a site label.
* **No external calls.** The narrative is deterministic and offline: no LLM, no API key, no
  egress. An LLM narrator is a documented seam (`Narrator` protocol), not a dependency.
* **Dependency surface**: fastapi, uvicorn, psycopg, pydantic on the server; react and react-dom
  in the browser.
* **CORS is intentionally absent**: the browser only talks to the Vite dev server, which proxies
  `/api`, so there is no cross-origin request to allow. If you ever call the API directly from a
  different origin, add an explicit allowlist — never `*` with credentials.

## Known limits / next steps

* Sensitivity is global (`BASELINE_WEEKS`), not per-account. Some customers will want to widen or
  tighten what counts as unusual.
* No drill-down: the location row is a dead end. The next click should be that location's weeks.
* Weekly cadence only. Daily anomaly detection would need a much better story for weekday effects
  and small counts than this MVP attempts.
* `baseline_weeks` is exposed for testing and support, not yet in the UI.
* `?as_of=YYYY-MM-DD` in the dashboard URL re-anchors the analysis (a support/demo
  override, badged "Custom date"). It is how you reproduce the June 3 incident in the UI:
  <http://localhost:5180/?account=6&as_of=2026-06-08>
