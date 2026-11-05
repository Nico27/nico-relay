# API contract (v1)

Base path: `/api/v1`. JSON only. Timestamps that name a day are `YYYY-MM-DD` **in the account's
timezone**; timestamps that name an instant are RFC 3339 in UTC (`2026-07-27T20:27:47Z`).

Money-free, auth-free MVP: one deployment per customer, so every endpoint is scoped by
`account_id` and there is no session. Wire auth/multi-tenancy here first when this leaves MVP
(see "Security notes" in README).

## `GET /healthz`

Liveness only, no DB. `200 {"status":"ok"}`.

## `GET /readyz`

Readiness: verifies the database answers. `200 {"status":"ok","database":"ok"}` or
`503 {"status":"degraded","database":"<error class>"}`.

## `GET /api/v1/accounts`

Roster for the account switcher.

```json
{
  "data_through": "2026-07-27",
  "accounts": [
    {
      "id": 1,
      "name": "Summit Auto Group",
      "industry": "Automotive Services",
      "timezone": "America/Chicago",
      "locations": ["Site A", "Site B", "Site C", "Site D", "Site E", "Site F"],
      "last_event_at": "2026-07-27T20:27:47Z",
      "event_count": 1223
    }
  ]
}
```

`data_through` is the newest event day across all accounts, in UTC terms (a plain date), or
`null` when the database has no events. `last_event_at` is `null` for an account with no events.

## `GET /api/v1/accounts/{account_id}/dashboard`

Query parameters:

| name | default | meaning |
| --- | --- | --- |
| `as_of` | newest available day | `YYYY-MM-DD`; clamps the analysis horizon. Values in the future or before the account existed are clamped. |
| `baseline_weeks` | `8` | 1–26; how many preceding weeks form the baseline. |

`404 {"detail":"Account not found"}` for an unknown id. `422` for malformed parameters (FastAPI
default body).

### Response

```jsonc
{
  "account": {"id": 6, "name": "Metro Collision Centers", "industry": "Automotive Services",
              "timezone": "America/New_York"},
  "generated_at": "2026-11-05T14:00:00Z",
  "data_through": "2026-07-27",
  "as_of_source": "latest_data",          // "latest_data" | "requested"
  "staleness_days": 101,                  // days between data_through and today; 0 when current
  "empty": false,                         // true when the account has no events at all
  "period": {
    "start": "2026-07-20",
    "end": "2026-07-26",
    "label": "Jul 20 – Jul 26",
    "day_count": 7,
    "baseline_weeks": 8,
    "reference_weeks_used": 8,
    "reference_weeks_skipped": 0
  },
  "headline": {
    "status": "within_typical",           // see status enum below
    "basis": "last_week",                 // "last_week" | "this_week" | null (empty account)
    "metric_key": "activity",
    "title": "Last week looked normal",
    "detail": "253 events against a usual 220–300."
  },
  "metrics": [ /* Metric[], always 6, fixed order */ ],
  "in_progress": {
    "start": "2026-07-27", "end": "2026-07-27",
    "label": "This week so far (1 day)",
    "day_count": 1,
    "partial": true,                      // the last day may still be filling up
    "metrics": [ /* Metric[] */ ]
  },
  "locations": [ /* Location[], sorted by |delta| desc, then name */ ],
  "drivers": [ /* Driver[], max 3, empty when nothing moved */ ],
  "narrative": "Last week looked normal: 253 against a usual 220–300. Every other measure stayed inside its usual range.",
  "data_quality": [ /* Note[] */ ]
}
```

### `headline.basis`

The headline answers "is this normal for us **now**", so it may speak about either window:

* `last_week` — the complete Monday–Sunday week. Stable, comparable, the Monday-morning view.
* `this_week` — the open week, used **only** when it has at least 2 days of data *and* its
  activity is outside its usual range. A Thursday should not be told "last week was fine"
  while this week is visibly abnormal.
* `null` — the account has no events at all.

`period`, `metrics` and `locations` always describe `period` (the complete week). `in_progress`
always describes the open week. `drivers` follow the headline: when `basis` is `this_week` they
are the open week's drivers, so the sentence and the numbers agree.

### `Metric`

```jsonc
{
  "key": "activity",          // activity | calls | missed_call_rate | leads | appointments | no_show_rate
  "label": "Activity",
  "unit": "events",           // "events" | "calls" | "percent"
  "kind": "volume",           // "volume" | "rate"
  "status": "within_typical", // enum below
  "current": 253,
  "typical": 260,             // median of the reference weeks; null when no baseline
  "low": 220,                 // usual range, inclusive ("usually 220–300"); null when no baseline
  "high": 300,
  "delta": -7,                // current - typical; null when no baseline
  "ratio": 0.97,              // current / typical; null when not computable (typical == 0)
  "numerator": 253,           // volume: current; rate: numerator count
  "denominator": null,        // volume: null; rate: denominator count
  "series": [                 // chronological, reference weeks then the current window last
    {"week_start": "2026-05-25", "value": 241, "current": false},
    {"week_start": "2026-07-20", "value": 253, "current": true}
  ],
  "note": null                // short human string for a caveat, e.g. "3% of calls had no outcome"
}
```

Rates carry `unit: "percent"` and a **0–100** value rounded to one decimal (e.g. `22.3`), while
`low`/`high`/`typical` use the same unit. Volumes are integers. The field names keep the
`…_typical` vocabulary for API stability; every customer-facing label says "usual" or "normal".

`series` is chronological, oldest first, and always ends with the current window (`current: true`).
A reference week whose rate denominator is too small to be meaningful is omitted from `series`
rather than plotted as a misleading number, so a rate series can be shorter than `baseline_weeks`.
When a metric has no usable baseline, `typical`, `low`, `high`, `delta` and `ratio` are all `null`
while `current` may still carry a value (a rate with real data but too little history).

### `Status` enum

| value | meaning |
| --- | --- |
| `above_typical` | outside the usual range, higher (UI: "Higher than usual") |
| `within_typical` | inside the usual range (UI: "Normal") |
| `below_typical` | outside the usual range, lower (UI: "Lower than usual") |
| `insufficient_history` | fewer than 4 usable reference weeks — we refuse to judge |
| `not_enough_data` | rate metric with too small a denominator (< 5) |
| `no_activity` | account has no events at all (headline only) |

### `Location`

```jsonc
{
  "location": "Site C",
  "status": "above_typical",   // verdict on activity
  "current": 76,               // activity in the period
  "typical": 14,
  "low": 9,
  "high": 20,
  "delta": 62,
  "ratio": 5.43,
  "share": 0.07,               // share of the total absolute deviation across locations, 0–1
  "calls": 40,
  "missed_rate": 22.5,         // 0–100 or null when the denominator is too small
  "missed_rate_status": "above_typical",
  "leads": 20,
  "appointments": 16,
  "no_show_rate": null,
  "note": null                 // e.g. "No activity in this period"
}
```

`typical`/`low`/`high`/`delta`/`ratio` are `null` when the location has no usable baseline.

### `Driver`

```jsonc
{"location": "Site C", "direction": "up", "delta": 62, "ratio": 5.43, "share": 0.07}
```

`direction` is `"up"` or `"down"`. Drivers are the up-to-3 locations with the largest
`|delta|` on activity, only when the account-level verdict is not `within_typical`.

### `Note`

```jsonc
{"code": "stale_data", "severity": "info", "message": "This view is based on data through Jul 27, 2026 (101 days ago)."}
```

Codes: `stale_data`, `outcome_gaps`, `no_recent_activity`, `reference_weeks_skipped`,
`reference_weeks_excluded`, `no_locations`, `location_silent`. `severity` is `"info"` or `"warning"`.

Exact duplicate events are removed once at ingest by the seed loader (it prints how many), so
they never reach this payload and there is no runtime note for them.
