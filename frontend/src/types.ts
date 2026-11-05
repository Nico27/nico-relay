/** Wire types. These mirror `docs/api.md` exactly — change them together. */

export type MetricStatus =
  | 'above_typical'
  | 'within_typical'
  | 'below_typical'
  | 'insufficient_history'
  | 'not_enough_data'
  | 'no_activity';

export type HeadlineBasis = 'last_week' | 'this_week' | null;

export interface AccountRef {
  id: number;
  name: string;
  industry: string;
  timezone: string;
}

export interface AccountSummary extends AccountRef {
  locations: string[];
  last_event_at: string | null;
  event_count: number;
}

export interface AccountsResponse {
  data_through: string | null;
  accounts: AccountSummary[];
}

export interface SeriesPoint {
  week_start: string;
  value: number;
  current: boolean;
}

export interface Metric {
  key: string;
  label: string;
  unit: 'events' | 'calls' | 'percent';
  kind: 'volume' | 'rate';
  status: MetricStatus;
  current: number | null;
  typical: number | null;
  low: number | null;
  high: number | null;
  delta: number | null;
  ratio: number | null;
  numerator: number;
  denominator: number | null;
  series: SeriesPoint[];
  note: string | null;
}

export interface Period {
  start: string;
  end: string;
  label: string;
  day_count: number;
  baseline_weeks: number;
  reference_weeks_used: number;
  reference_weeks_skipped: number;
}

export interface InProgress {
  start: string;
  end: string;
  label: string;
  day_count: number;
  partial: boolean;
  metrics: Metric[];
}

export interface Headline {
  status: MetricStatus;
  basis: HeadlineBasis;
  metric_key: string;
  title: string;
  detail: string;
}

export interface Location {
  location: string;
  status: MetricStatus;
  current: number;
  typical: number | null;
  low: number | null;
  high: number | null;
  delta: number | null;
  ratio: number | null;
  share: number | null;
  calls: number;
  missed_rate: number | null;
  missed_rate_status: MetricStatus;
  leads: number;
  appointments: number;
  no_show_rate: number | null;
  note: string | null;
}

export interface Driver {
  location: string;
  direction: 'up' | 'down';
  delta: number;
  ratio: number | null;
  share: number;
}

export interface Note {
  code: string;
  severity: 'info' | 'warning';
  message: string;
}

export interface DashboardResponse {
  account: AccountRef;
  generated_at: string;
  data_through: string;
  as_of_source: 'latest_data' | 'requested';
  staleness_days: number;
  empty: boolean;
  period: Period;
  headline: Headline;
  metrics: Metric[];
  in_progress: InProgress | null;
  locations: Location[];
  drivers: Driver[];
  narrative: string;
  data_quality: Note[];
}
