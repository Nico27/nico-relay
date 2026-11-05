# DASH-247 — Normal-activity dashboard (MVP)

Feature: help a customer admin answer "is this normal for us?" at a glance.
Stack: FastAPI + uv + pytest · React/TS + Vite + vitest · Postgres · Docker (non-root) + compose.
Decisions of record: `PLAN.md`. Wire contract: `docs/api.md`.

## Specs

- **S1 (question).** The dashboard must let a customer answer "is this normal for us?" at a glance, without exporting data or calling their account manager.
- **S2 (baseline).** "Normal" is the account's own recent history: up to 8 preceding weeks, sampled over the same weekday set as the window under judgement, robust-trimmed (median/MAD, drop refs >3σ) and presented as an observed typical range, not a single number.
- **S3 (windows).** Primary window is the last complete Monday–Sunday week in the account's timezone; a secondary "this week so far" window compares only matching weekdays. Partial weeks are never compared against full weeks.
- **S4 (verdicts).** Every metric reports one of `above_typical`, `within_typical`, `below_typical`, `insufficient_history`, `not_enough_data`; the account headline is `no_activity` when there are no events at all. Rates need ≥5 in the denominator and use a ±1.0pp floor.
- **S5 (multi-location).** The account view decomposes into per-location metrics sorted by contribution, plus up to 3 named drivers when the account is outside its typical range.
- **S6 (act on it).** The view must state what moved and where in one sentence (deterministic narrative), and must disclose data-quality caveats (staleness, outcome gaps, silent locations, skipped reference weeks).
- **S7 (messy data).** Exact duplicate events are dropped once at ingest with a printed report; `duration_seconds` is never used in a metric (unreliable for missed/voicemail); `NULL` outcomes are excluded from rate denominators and the gap is disclosed; an account with zero events renders a first-class empty state.
- **S8 (time).** All day bucketing happens in the account IANA timezone from UTC storage; when the newest data is older than today the response says `data_through` + `staleness_days` and the UI shows it, never a silent "this week is down".
- **S9 (non-goals).** No alerting/notifications, no forecasting or predictive ML, no cross-customer benchmarking. An LLM may narrate; it must never produce a number or a verdict, and the default path needs no API key.
- **S10 (stack constraints).** Backend FastAPI managed by uv, tested with pytest; frontend React/TypeScript with Vite, tested with vitest; Postgres with a real migration for `schema.sql` and a seed loader that handles `seed.sql`; one non-root API image and a docker-compose dev stack (local development only — no production deployment in scope).

## Tasks

- **T1** Product decisions (`PLAN.md`) + API contract (`docs/api.md`) — S1–S4, S9, S10.
- **T2** Migrations + seed loader (validate, dedupe, timezone-safe) — S7, S8, S10.
- **T3** Stats engine: windows, reference weeks, robust range, verdicts — S2, S3, S4 (pytest).
- **T4** Repository SQL + service assembly + FastAPI endpoints — S1, S5, S6, S8 (pytest).
- **T5** React dashboard against the contract — S1, S5, S6, S7 (vitest).
- **T6** Non-root image + docker-compose dev stack — S10.
- **T7** End-to-end verification on real seed data — S1–S8.

## Log

- **L1 (user, verbatim):** "We need to create an MVP in order to address one critical task (DASH-247): Help customers understand whether their recent activity is normal. Customers looking at their dashboard can't tell whether this week's numbers are good, bad, or typical for them. Product wants the dashboard to help a customer answer "is this normal for us?" at a glance, without exporting data or calling their account manager. Notes from product: probably involves comparing against some baseline, multi-location customers matter, a customer admin should be able to look at this Monday morning and act on it. Out of scope per product: alerting/notifications, and predictive ML/forecasting. (An LLM used for explanation, summarization, or classification is not forecasting — that's fair game) The ticket is deliberately light — that's realistic, not an oversight. Deciding what it actually means (what "normal" is, what window, what view) is part of the exercise. In order to do this, we will define the stack: -Backend: FastAPI with UV for managing the packages and pytest for testing. -Frontend: React/Typescript with Vite and vitest for testing. -Database: Postgres (we need to create a migration for schema.sql and handle seed.sql with its data accordingly since it might contain empty ranges, odd values, etc) -Docker: we need to align previous requirements with a docker image running with NO root user. We also need docker-compose for fast and easy development."
- **L2 (evidence, seed profile).** 20 accounts / 12,626 events / 2026-02-01 → 2026-07-27, UTC. Zero-event account (Quiet Harbor Spa). 12 exact-duplicate pairs. 313 NULL call durations, missed/voicemail avg ~740s. 398 NULL outcomes. Account 6 has 805 events on 2026-06-03 vs ~15/day (the anomaly to surface). Data ends on a Monday, 101 days before the current date → staleness is real, not hypothetical.
- **L3 (decision).** Self-baseline only, no peer benchmarking (S2). Last complete week primary, week-so-far secondary (S3). Deterministic narrator with an LLM-replaceable protocol (S9).
- **L4 (constraint).** Repository is not a git repository, so no work-unit commits were made; work units are reported as task checkpoints instead.
- **L5 (evidence, T2).** `python -m relay.migrate` applied `0001_init.sql`; `python -m relay.seed --reset` reported 20 accounts, 12,614 events, 12 exact duplicates dropped, 0 durations cleared.
- **L6 (evidence, T3/T4).** `uv run pytest -q` → 66 passed without a database; with `TEST_DATABASE_URL` → 76 passed (10 integration tests: dedupe counts, the June-3 incident as 804 events over 15 locations, outcome gaps, `02:00Z` Jul 28 bucketing to Jul 27 in Los Angeles).
- **L7 (decision, headline basis).** The headline describes the last complete week by default and switches to this-week-so-far when that window has ≥2 days of data and is outside its typical range; otherwise a Thursday admin reads "last week was fine" while the current week is abnormal. Asserted in `test_a_thursday_spike_leads_with_this_week_not_last_week`.
- **L8 (decision, tolerance).** Observed-range comparisons use a scale-aware tolerance: volumes 10% of the median (min 1 event), rates ±1.0pp. A flat 70/week history must not call 72 "above typical".
- **L9 (evidence, T5).** Frontend built inline after the delegated writer stalled: `npm run typecheck` clean, `npm test` → 41 tests across 4 files (formatters, sparkline geometry, components, App flows). Fixtures are generated from `docs/sample-payloads.json`, which is captured from the running backend, so the UI is tested against real payloads rather than invented ones.
- **L10 (verification, T6).** Dev stack up: `api` runs as uid 10001, migrations + seed on boot, `/readyz` reports the database. `scripts/verify.sh` covers backend tests, seed invariants, the contract, the June-3 detection and the non-root check.
- **L11 (evidence, T5 visual).** Rendered against the running API in light and dark: the June-3 account shows "Activity was above your typical week" (880 vs 46–93, 13.3×) with the top three sites named in the sentence and in the table; the zero-event account shows "No activity yet for Quiet Harbor Spa" instead of a misleading zero baseline.
- **L12 (user correction, verbatim):** "I don't want to have prod files or ready-prod files/changes. This is only for local dev. Keep it simple" — removed `docker-compose.prod.yml`, the production image stage, FastAPI static hosting (`STATIC_DIR`) and the `make prod`/`verify.sh --prod` paths; the API image keeps its non-root user.
- **L13 (decision, plain language).** The readout assumed statistical context ("typical 46–93", "13.33× your median", "above typical"). A support agent needs *is it fine, and if not why* — so the vocabulary changed at both layers: API copy now says "usual"/"normal"/"busier than usual" and rounds the multiplier ("about 13× a normal week"), and the UI adds a verdict the API does not compute — `summarise()` returns "All good last week" or "4 of 6 measures are unusual" (counting only measures that had a baseline), plus "Start here:" chips naming the sites. Charts became one bar per week with the usual range shaded and a caption reading `8 weeks ago → now`; the old line+band sparkline required knowing what a band meant. Verified by `format.test.ts` (labels, deltas, multipliers, `summarise`), rewritten `sparkline.test.ts` bar geometry, and 1440/600 px screenshots of both the anomalous and the normal account.
