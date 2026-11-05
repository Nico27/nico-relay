/**
 * Fixtures derived from the real API (`docs/sample-payloads.json`), which is captured
 * from a running backend against `seed.sql`. Do not hand-edit values here without
 * re-reading the contract in `docs/api.md`.
 */
import type { AccountsResponse, DashboardResponse } from '../types';

export const accountsResponse: AccountsResponse = {
  "data_through": "2026-07-27",
  "accounts": [
    {
      "id": 1,
      "name": "Summit Auto Group",
      "industry": "Automotive Services",
      "timezone": "America/Chicago",
      "locations": [
        "Site A",
        "Site B",
        "Site C",
        "Site D",
        "Site E",
        "Site F"
      ],
      "last_event_at": "2026-07-27T20:27:47Z",
      "event_count": 1221
    },
    {
      "id": 2,
      "name": "Harbor Dental Partners",
      "industry": "Dental",
      "timezone": "America/New_York",
      "locations": [
        "Site A",
        "Site B",
        "Site C"
      ],
      "last_event_at": "2026-07-26T20:04:27Z",
      "event_count": 729
    },
    {
      "id": 3,
      "name": "Bluebird HVAC",
      "industry": "Home Services",
      "timezone": "America/Denver",
      "locations": [
        "Site A",
        "Site B"
      ],
      "last_event_at": "2026-07-27T20:23:21Z",
      "event_count": 477
    },
    {
      "id": 4,
      "name": "Cornerstone Vet Clinics",
      "industry": "Veterinary",
      "timezone": "America/Chicago",
      "locations": [
        "Site A",
        "Site B",
        "Site C",
        "Site D"
      ],
      "last_event_at": "2026-07-27T19:07:29Z",
      "event_count": 796
    },
    {
      "id": 5,
      "name": "Pacific Smiles",
      "industry": "Dental",
      "timezone": "America/Los_Angeles",
      "locations": [
        "Site A",
        "Site B",
        "Site C",
        "Site D",
        "Site E"
      ],
      "last_event_at": "2026-07-27T20:18:43Z",
      "event_count": 884
    },
    {
      "id": 6,
      "name": "Metro Collision Centers",
      "industry": "Automotive Services",
      "timezone": "America/New_York",
      "locations": [
        "Site A",
        "Site B",
        "Site C",
        "Site D",
        "Site E",
        "Site F",
        "Site G",
        "Site H",
        "Site I",
        "Site J",
        "Site K",
        "Site L",
        "Site M",
        "Site N",
        "Site O"
      ],
      "last_event_at": "2026-07-27T19:15:33Z",
      "event_count": 2637
    },
    {
      "id": 7,
      "name": "Desert Springs Plumbing",
      "industry": "Home Services",
      "timezone": "America/Phoenix",
      "locations": [
        "Site A",
        "Site B"
      ],
      "last_event_at": "2026-07-27T14:58:39Z",
      "event_count": 437
    },
    {
      "id": 8,
      "name": "Lakeside Physio",
      "industry": "Healthcare",
      "timezone": "America/Chicago",
      "locations": [
        "Site A"
      ],
      "last_event_at": "2026-07-24T17:30:25Z",
      "event_count": 260
    },
    {
      "id": 9,
      "name": "Ironwood Fitness",
      "industry": "Fitness",
      "timezone": "America/Denver",
      "locations": [
        "Site A",
        "Site B",
        "Site C"
      ],
      "last_event_at": "2026-07-27T21:34:36Z",
      "event_count": 546
    },
    {
      "id": 10,
      "name": "Gulf Coast Roofing",
      "industry": "Home Services",
      "timezone": "America/Chicago",
      "locations": [
        "Site A",
        "Site B"
      ],
      "last_event_at": "2026-07-27T22:20:34Z",
      "event_count": 342
    },
    {
      "id": 11,
      "name": "Northgate Optical",
      "industry": "Healthcare",
      "timezone": "America/New_York",
      "locations": [
        "Site A",
        "Site B"
      ],
      "last_event_at": "2026-07-27T15:04:06Z",
      "event_count": 354
    },
    {
      "id": 12,
      "name": "Redline Tire & Service",
      "industry": "Automotive Services",
      "timezone": "America/Los_Angeles",
      "locations": [
        "Site A",
        "Site B",
        "Site C",
        "Site D",
        "Site E",
        "Site F",
        "Site G"
      ],
      "last_event_at": "2026-07-27T21:09:18Z",
      "event_count": 1303
    },
    {
      "id": 13,
      "name": "Willow Creek Counseling",
      "industry": "Healthcare",
      "timezone": "America/Chicago",
      "locations": [
        "Site A"
      ],
      "last_event_at": "2026-07-27T17:33:26Z",
      "event_count": 205
    },
    {
      "id": 14,
      "name": "Beacon Home Security",
      "industry": "Home Services",
      "timezone": "America/New_York",
      "locations": [
        "Site A",
        "Site B",
        "Site C",
        "Site D"
      ],
      "last_event_at": "2026-07-27T20:50:26Z",
      "event_count": 638
    },
    {
      "id": 15,
      "name": "Sierra Pest Solutions",
      "industry": "Home Services",
      "timezone": "America/Phoenix",
      "locations": [
        "Site A",
        "Site B",
        "Site C"
      ],
      "last_event_at": "2026-07-27T17:42:39Z",
      "event_count": 499
    },
    {
      "id": 16,
      "name": "Old Town Barbers",
      "industry": "Personal Care",
      "timezone": "America/Chicago",
      "locations": [
        "Site A"
      ],
      "last_event_at": "2026-07-27T16:28:51Z",
      "event_count": 167
    },
    {
      "id": 17,
      "name": "Evergreen Landscaping",
      "industry": "Home Services",
      "timezone": "America/Los_Angeles",
      "locations": [
        "Site A",
        "Site B"
      ],
      "last_event_at": "2026-07-27T22:00:29Z",
      "event_count": 323
    },
    {
      "id": 18,
      "name": "Capital City Storage",
      "industry": "Storage",
      "timezone": "UTC",
      "locations": [
        "Site A",
        "Site B",
        "Site C",
        "Site D",
        "Site E"
      ],
      "last_event_at": "2026-07-27T15:13:35Z",
      "event_count": 586
    },
    {
      "id": 19,
      "name": "Riverbend Chiropractic",
      "industry": "Healthcare",
      "timezone": "America/New_York",
      "locations": [
        "Site A"
      ],
      "last_event_at": "2026-07-27T15:16:44Z",
      "event_count": 210
    },
    {
      "id": 20,
      "name": "Quiet Harbor Spa",
      "industry": "Personal Care",
      "timezone": "America/Los_Angeles",
      "locations": [],
      "last_event_at": null,
      "event_count": 0
    }
  ]
};

export const metroDashboard: DashboardResponse = {
  "account": {
    "id": 6,
    "name": "Metro Collision Centers",
    "industry": "Automotive Services",
    "timezone": "America/New_York"
  },
  "generated_at": "2026-11-05T20:12:33.973544Z",
  "data_through": "2026-06-08",
  "as_of_source": "requested",
  "staleness_days": 150,
  "empty": false,
  "period": {
    "start": "2026-06-01",
    "end": "2026-06-07",
    "label": "Jun 1 \u2013 Jun 7",
    "day_count": 7,
    "baseline_weeks": 8,
    "reference_weeks_used": 8,
    "reference_weeks_skipped": 0
  },
  "headline": {
    "status": "above_typical",
    "basis": "last_week",
    "metric_key": "activity",
    "title": "Last week was busier than usual",
    "detail": "880 events against a usual 46\u201393."
  },
  "metrics": [
    {
      "key": "activity",
      "label": "Activity",
      "unit": "events",
      "kind": "volume",
      "status": "above_typical",
      "current": 880,
      "typical": 66,
      "low": 46,
      "high": 93,
      "delta": 814,
      "ratio": 13.33,
      "numerator": 880,
      "denominator": null,
      "series": [
        {
          "week_start": "2026-05-11",
          "value": 78,
          "current": false
        },
        {
          "week_start": "2026-05-18",
          "value": 62,
          "current": false
        },
        {
          "week_start": "2026-05-25",
          "value": 53,
          "current": false
        },
        {
          "week_start": "2026-06-01",
          "value": 880,
          "current": true
        }
      ],
      "note": null
    },
    {
      "key": "calls",
      "label": "Calls received",
      "unit": "calls",
      "kind": "volume",
      "status": "above_typical",
      "current": 528,
      "typical": 40,
      "low": 25,
      "high": 53,
      "delta": 488,
      "ratio": 13.04,
      "numerator": 528,
      "denominator": null,
      "series": [
        {
          "week_start": "2026-05-11",
          "value": 46,
          "current": false
        },
        {
          "week_start": "2026-05-18",
          "value": 38,
          "current": false
        },
        {
          "week_start": "2026-05-25",
          "value": 29,
          "current": false
        },
        {
          "week_start": "2026-06-01",
          "value": 528,
          "current": true
        }
      ],
      "note": null
    },
    {
      "key": "missed_call_rate",
      "label": "Missed-call rate",
      "unit": "percent",
      "kind": "rate",
      "status": "within_typical",
      "current": 23.3,
      "typical": 26.4,
      "low": 13.7,
      "high": 33.4,
      "delta": -3.099999999999998,
      "ratio": 0.88,
      "numerator": 120,
      "denominator": 514,
      "series": [
        {
          "week_start": "2026-05-11",
          "value": 21.7,
          "current": false
        },
        {
          "week_start": "2026-05-18",
          "value": 32.4,
          "current": false
        },
        {
          "week_start": "2026-05-25",
          "value": 31.0,
          "current": false
        },
        {
          "week_start": "2026-06-01",
          "value": 23.3,
          "current": true
        }
      ],
      "note": "14 of 528 calls had no outcome and are excluded from this rate."
    },
    {
      "key": "leads",
      "label": "Leads created",
      "unit": "events",
      "kind": "volume",
      "status": "above_typical",
      "current": 230,
      "typical": 16,
      "low": 10,
      "high": 24,
      "delta": 214,
      "ratio": 13.94,
      "numerator": 230,
      "denominator": null,
      "series": [
        {
          "week_start": "2026-05-11",
          "value": 22,
          "current": false
        },
        {
          "week_start": "2026-05-18",
          "value": 17,
          "current": false
        },
        {
          "week_start": "2026-05-25",
          "value": 15,
          "current": false
        },
        {
          "week_start": "2026-06-01",
          "value": 230,
          "current": true
        }
      ],
      "note": null
    },
    {
      "key": "appointments",
      "label": "Appointments set",
      "unit": "events",
      "kind": "volume",
      "status": "above_typical",
      "current": 122,
      "typical": 10,
      "low": 5,
      "high": 16,
      "delta": 112,
      "ratio": 12.2,
      "numerator": 122,
      "denominator": null,
      "series": [
        {
          "week_start": "2026-05-11",
          "value": 10,
          "current": false
        },
        {
          "week_start": "2026-05-18",
          "value": 7,
          "current": false
        },
        {
          "week_start": "2026-05-25",
          "value": 9,
          "current": false
        },
        {
          "week_start": "2026-06-01",
          "value": 122,
          "current": true
        }
      ],
      "note": null
    },
    {
      "key": "no_show_rate",
      "label": "No-show rate",
      "unit": "percent",
      "kind": "rate",
      "status": "within_typical",
      "current": 14.2,
      "typical": 22.2,
      "low": 8.1,
      "high": 29.6,
      "delta": -8.0,
      "ratio": 0.64,
      "numerator": 17,
      "denominator": 120,
      "series": [
        {
          "week_start": "2026-05-11",
          "value": 55.6,
          "current": false
        },
        {
          "week_start": "2026-05-18",
          "value": 28.6,
          "current": false
        },
        {
          "week_start": "2026-05-25",
          "value": 22.2,
          "current": false
        },
        {
          "week_start": "2026-06-01",
          "value": 14.2,
          "current": true
        }
      ],
      "note": "2 of 122 appointments had no outcome and are excluded from this rate."
    }
  ],
  "in_progress": {
    "start": "2026-06-08",
    "end": "2026-06-08",
    "label": "This week so far (1 day)",
    "day_count": 1,
    "partial": true,
    "metrics": [
      {
        "key": "activity",
        "label": "Activity",
        "unit": "events",
        "kind": "volume",
        "status": "within_typical",
        "current": 17,
        "typical": 10,
        "low": 0,
        "high": 29,
        "delta": 8,
        "ratio": 1.79,
        "numerator": 17,
        "denominator": null,
        "series": [
          {
            "week_start": "2026-05-18",
            "value": 9,
            "current": false
          },
          {
            "week_start": "2026-05-25",
            "value": 10,
            "current": false
          },
          {
            "week_start": "2026-06-01",
            "value": 16,
            "current": false
          },
          {
            "week_start": "2026-06-08",
            "value": 17,
            "current": true
          }
        ],
        "note": null
      },
      {
        "key": "calls",
        "label": "Calls received",
        "unit": "calls",
        "kind": "volume",
        "status": "within_typical",
        "current": 10,
        "typical": 6,
        "low": 0,
        "high": 18,
        "delta": 4,
        "ratio": 1.67,
        "numerator": 10,
        "denominator": null,
        "series": [
          {
            "week_start": "2026-05-18",
            "value": 7,
            "current": false
          },
          {
            "week_start": "2026-05-25",
            "value": 5,
            "current": false
          },
          {
            "week_start": "2026-06-01",
            "value": 11,
            "current": false
          },
          {
            "week_start": "2026-06-08",
            "value": 10,
            "current": true
          }
        ],
        "note": null
      },
      {
        "key": "missed_call_rate",
        "label": "Missed-call rate",
        "unit": "percent",
        "kind": "rate",
        "status": "within_typical",
        "current": 10.0,
        "typical": 18.35,
        "low": 0.0,
        "high": 61.0,
        "delta": -8.350000000000001,
        "ratio": 0.54,
        "numerator": 1,
        "denominator": 10,
        "series": [
          {
            "week_start": "2026-05-18",
            "value": 57.1,
            "current": false
          },
          {
            "week_start": "2026-05-25",
            "value": 60.0,
            "current": false
          },
          {
            "week_start": "2026-06-01",
            "value": 0.0,
            "current": false
          },
          {
            "week_start": "2026-06-08",
            "value": 10.0,
            "current": true
          }
        ],
        "note": null
      },
      {
        "key": "leads",
        "label": "Leads created",
        "unit": "events",
        "kind": "volume",
        "status": "within_typical",
        "current": 5,
        "typical": 2,
        "low": 0,
        "high": 8,
        "delta": 2,
        "ratio": 2.0,
        "numerator": 5,
        "denominator": null,
        "series": [
          {
            "week_start": "2026-05-18",
            "value": 0,
            "current": false
          },
          {
            "week_start": "2026-05-25",
            "value": 4,
            "current": false
          },
          {
            "week_start": "2026-06-01",
            "value": 4,
            "current": false
          },
          {
            "week_start": "2026-06-08",
            "value": 5,
            "current": true
          }
        ],
        "note": null
      },
      {
        "key": "appointments",
        "label": "Appointments set",
        "unit": "events",
        "kind": "volume",
        "status": "within_typical",
        "current": 2,
        "typical": 2,
        "low": 0,
        "high": 5,
        "delta": 0,
        "ratio": 1.33,
        "numerator": 2,
        "denominator": null,
        "series": [
          {
            "week_start": "2026-05-18",
            "value": 2,
            "current": false
          },
          {
            "week_start": "2026-05-25",
            "value": 1,
            "current": false
          },
          {
            "week_start": "2026-06-01",
            "value": 1,
            "current": false
          },
          {
            "week_start": "2026-06-08",
            "value": 2,
            "current": true
          }
        ],
        "note": null
      },
      {
        "key": "no_show_rate",
        "label": "No-show rate",
        "unit": "percent",
        "kind": "rate",
        "status": "insufficient_history",
        "current": null,
        "typical": null,
        "low": null,
        "high": null,
        "delta": null,
        "ratio": null,
        "numerator": 1,
        "denominator": 2,
        "series": [],
        "note": null
      }
    ]
  },
  "locations": [
    {
      "location": "Site N",
      "status": "above_typical",
      "current": 72,
      "typical": 4,
      "low": 0,
      "high": 9,
      "delta": 68,
      "ratio": 18.0,
      "share": 0.0833,
      "calls": 33,
      "missed_rate": 21.9,
      "missed_rate_status": "insufficient_history",
      "leads": 20,
      "appointments": 19,
      "no_show_rate": 16.7,
      "note": null
    },
    {
      "location": "Site D",
      "status": "above_typical",
      "current": 70,
      "typical": 4,
      "low": 2,
      "high": 8,
      "delta": 66,
      "ratio": 15.56,
      "share": 0.0809,
      "calls": 38,
      "missed_rate": 29.7,
      "missed_rate_status": "insufficient_history",
      "leads": 25,
      "appointments": 7,
      "no_show_rate": 14.3,
      "note": null
    },
    {
      "location": "Site C",
      "status": "above_typical",
      "current": 67,
      "typical": 3,
      "low": 1,
      "high": 6,
      "delta": 64,
      "ratio": 22.33,
      "share": 0.0784,
      "calls": 40,
      "missed_rate": 27.5,
      "missed_rate_status": "insufficient_history",
      "leads": 13,
      "appointments": 14,
      "no_show_rate": 7.1,
      "note": null
    },
    {
      "location": "Site L",
      "status": "above_typical",
      "current": 67,
      "typical": 5,
      "low": 0,
      "high": 12,
      "delta": 62,
      "ratio": 13.4,
      "share": 0.076,
      "calls": 51,
      "missed_rate": 22.4,
      "missed_rate_status": "insufficient_history",
      "leads": 12,
      "appointments": 4,
      "no_show_rate": null,
      "note": null
    },
    {
      "location": "Site B",
      "status": "above_typical",
      "current": 65,
      "typical": 4,
      "low": 1,
      "high": 10,
      "delta": 61,
      "ratio": 16.25,
      "share": 0.0748,
      "calls": 41,
      "missed_rate": 20.5,
      "missed_rate_status": "insufficient_history",
      "leads": 16,
      "appointments": 8,
      "no_show_rate": 0.0,
      "note": null
    },
    {
      "location": "Site F",
      "status": "above_typical",
      "current": 65,
      "typical": 4,
      "low": 1,
      "high": 8,
      "delta": 60,
      "ratio": 14.44,
      "share": 0.0735,
      "calls": 42,
      "missed_rate": 23.8,
      "missed_rate_status": "insufficient_history",
      "leads": 16,
      "appointments": 7,
      "no_show_rate": 28.6,
      "note": null
    },
    {
      "location": "Site K",
      "status": "above_typical",
      "current": 60,
      "typical": 4,
      "low": 2,
      "high": 7,
      "delta": 56,
      "ratio": 13.33,
      "share": 0.0686,
      "calls": 33,
      "missed_rate": 22.6,
      "missed_rate_status": "insufficient_history",
      "leads": 19,
      "appointments": 8,
      "no_show_rate": 12.5,
      "note": null
    },
    {
      "location": "Site G",
      "status": "above_typical",
      "current": 57,
      "typical": 4,
      "low": 0,
      "high": 8,
      "delta": 54,
      "ratio": 16.29,
      "share": 0.0662,
      "calls": 35,
      "missed_rate": 14.7,
      "missed_rate_status": "insufficient_history",
      "leads": 12,
      "appointments": 10,
      "no_show_rate": 11.1,
      "note": null
    },
    {
      "location": "Site J",
      "status": "above_typical",
      "current": 56,
      "typical": 5,
      "low": 2,
      "high": 8,
      "delta": 51,
      "ratio": 11.2,
      "share": 0.0625,
      "calls": 31,
      "missed_rate": 26.7,
      "missed_rate_status": "insufficient_history",
      "leads": 14,
      "appointments": 11,
      "no_show_rate": 9.1,
      "note": null
    },
    {
      "location": "Site H",
      "status": "above_typical",
      "current": 54,
      "typical": 4,
      "low": 0,
      "high": 7,
      "delta": 50,
      "ratio": 15.43,
      "share": 0.0613,
      "calls": 31,
      "missed_rate": 12.9,
      "missed_rate_status": "insufficient_history",
      "leads": 15,
      "appointments": 8,
      "no_show_rate": 25.0,
      "note": null
    },
    {
      "location": "Site E",
      "status": "above_typical",
      "current": 55,
      "typical": 6,
      "low": 2,
      "high": 10,
      "delta": 48,
      "ratio": 8.46,
      "share": 0.0588,
      "calls": 34,
      "missed_rate": 26.5,
      "missed_rate_status": "insufficient_history",
      "leads": 16,
      "appointments": 5,
      "no_show_rate": 0.0,
      "note": null
    },
    {
      "location": "Site M",
      "status": "above_typical",
      "current": 50,
      "typical": 4,
      "low": 1,
      "high": 6,
      "delta": 46,
      "ratio": 14.29,
      "share": 0.0564,
      "calls": 29,
      "missed_rate": 14.8,
      "missed_rate_status": "insufficient_history",
      "leads": 15,
      "appointments": 6,
      "no_show_rate": 33.3,
      "note": null
    },
    {
      "location": "Site A",
      "status": "above_typical",
      "current": 49,
      "typical": 4,
      "low": 1,
      "high": 9,
      "delta": 44,
      "ratio": 10.89,
      "share": 0.0539,
      "calls": 26,
      "missed_rate": 11.5,
      "missed_rate_status": "insufficient_history",
      "leads": 15,
      "appointments": 8,
      "no_show_rate": 12.5,
      "note": null
    },
    {
      "location": "Site I",
      "status": "above_typical",
      "current": 47,
      "typical": 3,
      "low": 0,
      "high": 6,
      "delta": 44,
      "ratio": 15.67,
      "share": 0.0539,
      "calls": 33,
      "missed_rate": 40.6,
      "missed_rate_status": "insufficient_history",
      "leads": 9,
      "appointments": 5,
      "no_show_rate": 20.0,
      "note": null
    },
    {
      "location": "Site O",
      "status": "above_typical",
      "current": 46,
      "typical": 4,
      "low": 2,
      "high": 5,
      "delta": 42,
      "ratio": 13.14,
      "share": 0.0515,
      "calls": 31,
      "missed_rate": 30.0,
      "missed_rate_status": "insufficient_history",
      "leads": 13,
      "appointments": 2,
      "no_show_rate": null,
      "note": null
    }
  ],
  "drivers": [
    {
      "location": "Site N",
      "direction": "up",
      "delta": 68,
      "ratio": 18.0,
      "share": 0.0833
    },
    {
      "location": "Site D",
      "direction": "up",
      "delta": 66,
      "ratio": 15.56,
      "share": 0.0809
    },
    {
      "location": "Site C",
      "direction": "up",
      "delta": 64,
      "ratio": 22.33,
      "share": 0.0784
    }
  ],
  "narrative": "Last week was busier than usual: 880 against a usual 46\u201393 \u2014 about 13\u00d7 a normal week. Calls received was higher than usual at 528 (usually 25\u201353). Leads created was higher than usual at 230 (usually 10\u201324). Appointments set was higher than usual at 122 (usually 5\u201316). Most of the change came from Site N (+68), Site D (+66) and Site C (+64).",
  "data_quality": [
    {
      "code": "stale_data",
      "severity": "warning",
      "message": "This view is based on data through Jun 8, 150 days ago."
    },
    {
      "code": "outcome_gaps",
      "severity": "info",
      "message": "14 of 528 calls in this period (3%) had no recorded outcome, so the missed-call rate covers the rest."
    }
  ]
};

export const quietHarborDashboard: DashboardResponse = {
  "account": {
    "id": 20,
    "name": "Quiet Harbor Spa",
    "industry": "Personal Care",
    "timezone": "America/Los_Angeles"
  },
  "generated_at": "2026-11-05T20:12:33.980266Z",
  "data_through": "2026-07-27",
  "as_of_source": "latest_data",
  "staleness_days": 101,
  "empty": true,
  "period": {
    "start": "2026-07-20",
    "end": "2026-07-26",
    "label": "Jul 20 \u2013 Jul 26",
    "day_count": 7,
    "baseline_weeks": 8,
    "reference_weeks_used": 0,
    "reference_weeks_skipped": 0
  },
  "headline": {
    "status": "no_activity",
    "basis": null,
    "metric_key": "activity",
    "title": "No activity yet",
    "detail": "We haven't received any events for this account yet."
  },
  "metrics": [
    {
      "key": "activity",
      "label": "Activity",
      "unit": "events",
      "kind": "volume",
      "status": "insufficient_history",
      "current": 0,
      "typical": null,
      "low": null,
      "high": null,
      "delta": null,
      "ratio": null,
      "numerator": 0,
      "denominator": null,
      "series": [
        {
          "week_start": "2026-07-20",
          "value": 0,
          "current": true
        }
      ],
      "note": null
    },
    {
      "key": "calls",
      "label": "Calls received",
      "unit": "calls",
      "kind": "volume",
      "status": "insufficient_history",
      "current": 0,
      "typical": null,
      "low": null,
      "high": null,
      "delta": null,
      "ratio": null,
      "numerator": 0,
      "denominator": null,
      "series": [
        {
          "week_start": "2026-07-20",
          "value": 0,
          "current": true
        }
      ],
      "note": null
    },
    {
      "key": "missed_call_rate",
      "label": "Missed-call rate",
      "unit": "percent",
      "kind": "rate",
      "status": "insufficient_history",
      "current": null,
      "typical": null,
      "low": null,
      "high": null,
      "delta": null,
      "ratio": null,
      "numerator": 0,
      "denominator": 0,
      "series": [],
      "note": null
    },
    {
      "key": "leads",
      "label": "Leads created",
      "unit": "events",
      "kind": "volume",
      "status": "insufficient_history",
      "current": 0,
      "typical": null,
      "low": null,
      "high": null,
      "delta": null,
      "ratio": null,
      "numerator": 0,
      "denominator": null,
      "series": [
        {
          "week_start": "2026-07-20",
          "value": 0,
          "current": true
        }
      ],
      "note": null
    },
    {
      "key": "appointments",
      "label": "Appointments set",
      "unit": "events",
      "kind": "volume",
      "status": "insufficient_history",
      "current": 0,
      "typical": null,
      "low": null,
      "high": null,
      "delta": null,
      "ratio": null,
      "numerator": 0,
      "denominator": null,
      "series": [
        {
          "week_start": "2026-07-20",
          "value": 0,
          "current": true
        }
      ],
      "note": null
    },
    {
      "key": "no_show_rate",
      "label": "No-show rate",
      "unit": "percent",
      "kind": "rate",
      "status": "insufficient_history",
      "current": null,
      "typical": null,
      "low": null,
      "high": null,
      "delta": null,
      "ratio": null,
      "numerator": 0,
      "denominator": 0,
      "series": [],
      "note": null
    }
  ],
  "in_progress": {
    "start": "2026-07-27",
    "end": "2026-07-27",
    "label": "This week so far (1 day)",
    "day_count": 1,
    "partial": true,
    "metrics": [
      {
        "key": "activity",
        "label": "Activity",
        "unit": "events",
        "kind": "volume",
        "status": "insufficient_history",
        "current": 0,
        "typical": null,
        "low": null,
        "high": null,
        "delta": null,
        "ratio": null,
        "numerator": 0,
        "denominator": null,
        "series": [
          {
            "week_start": "2026-07-27",
            "value": 0,
            "current": true
          }
        ],
        "note": null
      },
      {
        "key": "calls",
        "label": "Calls received",
        "unit": "calls",
        "kind": "volume",
        "status": "insufficient_history",
        "current": 0,
        "typical": null,
        "low": null,
        "high": null,
        "delta": null,
        "ratio": null,
        "numerator": 0,
        "denominator": null,
        "series": [
          {
            "week_start": "2026-07-27",
            "value": 0,
            "current": true
          }
        ],
        "note": null
      },
      {
        "key": "missed_call_rate",
        "label": "Missed-call rate",
        "unit": "percent",
        "kind": "rate",
        "status": "insufficient_history",
        "current": null,
        "typical": null,
        "low": null,
        "high": null,
        "delta": null,
        "ratio": null,
        "numerator": 0,
        "denominator": 0,
        "series": [],
        "note": null
      },
      {
        "key": "leads",
        "label": "Leads created",
        "unit": "events",
        "kind": "volume",
        "status": "insufficient_history",
        "current": 0,
        "typical": null,
        "low": null,
        "high": null,
        "delta": null,
        "ratio": null,
        "numerator": 0,
        "denominator": null,
        "series": [
          {
            "week_start": "2026-07-27",
            "value": 0,
            "current": true
          }
        ],
        "note": null
      },
      {
        "key": "appointments",
        "label": "Appointments set",
        "unit": "events",
        "kind": "volume",
        "status": "insufficient_history",
        "current": 0,
        "typical": null,
        "low": null,
        "high": null,
        "delta": null,
        "ratio": null,
        "numerator": 0,
        "denominator": null,
        "series": [
          {
            "week_start": "2026-07-27",
            "value": 0,
            "current": true
          }
        ],
        "note": null
      },
      {
        "key": "no_show_rate",
        "label": "No-show rate",
        "unit": "percent",
        "kind": "rate",
        "status": "insufficient_history",
        "current": null,
        "typical": null,
        "low": null,
        "high": null,
        "delta": null,
        "ratio": null,
        "numerator": 0,
        "denominator": 0,
        "series": [],
        "note": null
      }
    ]
  },
  "locations": [],
  "drivers": [],
  "narrative": "We haven't received any activity from Quiet Harbor Spa yet. Once events arrive, this page will show whether a week is typical for you.",
  "data_quality": [
    {
      "code": "stale_data",
      "severity": "warning",
      "message": "This view is based on data through Jul 27, 101 days ago."
    },
    {
      "code": "no_locations",
      "severity": "info",
      "message": "No locations have reported for this account yet."
    }
  ]
};
