import type { Metric, MetricStatus } from './types';

const MINUS = '\u2212';
const EN_DASH = '\u2013';

const integerFormatter = new Intl.NumberFormat('en-US', { maximumFractionDigits: 0 });
const oneDecimalFormatter = new Intl.NumberFormat('en-US', {
  minimumFractionDigits: 1,
  maximumFractionDigits: 1,
});

export function formatNumber(value: number | null | undefined): string {
  if (value === null || value === undefined || Number.isNaN(value)) return '—';
  return integerFormatter.format(value);
}

export function formatPercent(value: number | null | undefined): string {
  if (value === null || value === undefined || Number.isNaN(value)) return '—';
  return `${oneDecimalFormatter.format(value)}%`;
}

export function formatDelta(value: number | null | undefined): string {
  if (value === null || value === undefined || Number.isNaN(value)) return '—';
  const rounded = Math.round(value);
  if (rounded === 0) return '0';
  return rounded > 0 ? `+${formatNumber(rounded)}` : `${MINUS}${formatNumber(Math.abs(rounded))}`;
}

export function formatRatio(value: number | null | undefined): string {
  if (value === null || value === undefined || Number.isNaN(value)) return '—';
  if (Number.isInteger(value)) return `${value}\u00d7`;
  return `${oneDecimalFormatter.format(value)}\u00d7`;
}

function parseDay(iso: string): Date {
  return new Date(`${iso}T00:00:00Z`);
}

export function formatDay(iso: string): string {
  return parseDay(iso).toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric',
    timeZone: 'UTC',
  });
}

export function formatDateLong(iso: string): string {
  return parseDay(iso).toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
    timeZone: 'UTC',
  });
}

type Rangeable = Pick<Metric, 'unit' | 'low' | 'high'>;

export function formatRange(metric: Rangeable): string {
  if (metric.low === null || metric.high === null) return '—';
  if (metric.unit === 'percent') {
    return `${oneDecimalFormatter.format(metric.low)}${EN_DASH}${oneDecimalFormatter.format(
      metric.high,
    )}%`;
  }
  return `${formatNumber(metric.low)}${EN_DASH}${formatNumber(metric.high)}`;
}

export function formatMetricValue(metric: Pick<Metric, 'unit' | 'current'>): string {
  if (metric.current === null) return '—';
  return metric.unit === 'percent'
    ? oneDecimalFormatter.format(metric.current) + '%'
    : formatNumber(metric.current);
}

export function formatTypical(metric: Rangeable & Pick<Metric, 'typical'>): string | null {
  if (metric.typical === null) return null;
  if (metric.unit === 'percent') return `${oneDecimalFormatter.format(metric.typical)}%`;
  return formatNumber(metric.typical);
}

export function metricUnitNoun(metric: Pick<Metric, 'unit'>): string {
  return metric.unit === 'percent' ? 'of activity' : metric.unit;
}

// Plain words for a support agent, not statistical words for an analyst.
const STATUS_LABELS: Record<MetricStatus, string> = {
  above_typical: 'Higher than usual',
  within_typical: 'Normal',
  below_typical: 'Lower than usual',
  insufficient_history: 'Not enough history yet',
  not_enough_data: 'Not enough data yet',
  no_activity: 'No activity',
};

export function statusLabel(status: MetricStatus): string {
  return STATUS_LABELS[status] ?? status;
}

const STATUS_GLYPHS: Record<MetricStatus, string> = {
  above_typical: '\u25b2',
  below_typical: '\u25bc',
  within_typical: '\u25cf',
  insufficient_history: '\u25cc',
  not_enough_data: '\u25cc',
  no_activity: '\u25cb',
};

export function statusGlyph(status: MetricStatus): string {
  return STATUS_GLYPHS[status] ?? '\u25cf';
}

export type Tone = 'above' | 'below' | 'normal' | 'muted' | 'empty';

export function statusTone(status: MetricStatus): Tone {
  switch (status) {
    case 'above_typical':
      return 'above';
    case 'below_typical':
      return 'below';
    case 'within_typical':
      return 'normal';
    case 'no_activity':
      return 'empty';
    default:
      return 'muted';
  }
}

/** "814 more than usual" / "3 fewer than usual" — never a bare arrow or "median". */
export function describeDelta(metric: Metric): string {
  if (metric.delta === null || metric.typical === null) return 'Nothing to compare with yet';
  const rounded = Math.round(metric.delta);
  if (rounded === 0) return 'right at the usual level';
  return rounded > 0
    ? `${formatNumber(rounded)} more than usual`
    : `${formatNumber(Math.abs(rounded))} fewer than usual`;
}

/** "usually 46–93" — the sentence a person would actually say. */
export function usualRange(metric: Pick<Metric, 'unit' | 'low' | 'high'>): string | null {
  const range = formatRange(metric);
  return range === '—' ? null : `usually ${range}`;
}

/** "about 13× a normal week" — rounds rather than implying precision. */
export function describeMultiple(ratio: number | null): string | null {
  if (ratio === null || !Number.isFinite(ratio)) return null;
  const label = ratio >= 10 ? `${Math.round(ratio)}` : formatRatio(ratio).replace('×', '');
  return `about ${label}× a normal week`;
}

export type VerdictTone = 'normal' | 'attention' | 'unknown';

export interface Verdict {
  tone: VerdictTone;
  heading: string;
  supporting: string;
  focus: Array<{ location: string; delta: number }>;
}

const DEVIATING: MetricStatus[] = ['above_typical', 'below_typical'];

/**
 * The one thing a support agent needs first: are we fine, and if not, how much of
 * it is off and where. Counts only the measures we could actually judge, so
 * "2 of 6" is never inflated by metrics that had no baseline.
 */
export function summarise(
  dashboard: {
    empty: boolean;
    headline: { basis: 'last_week' | 'this_week' | null };
    metrics: Metric[];
    in_progress: { metrics: Metric[] } | null;
    drivers: Array<{ location: string; delta: number }>;
    period: { baseline_weeks: number };
  },
): Verdict {
  const thisWeek = dashboard.headline.basis === 'this_week';
  const week =
    thisWeek && dashboard.in_progress ? dashboard.in_progress.metrics : dashboard.metrics;
  const soFar = thisWeek ? ' so far' : '';

  if (dashboard.empty) {
    return { tone: 'unknown', heading: 'No activity yet', supporting: '', focus: [] };
  }

  const assessed = week.filter((metric) => metric.low !== null && metric.high !== null);
  const out = assessed.filter((metric) => DEVIATING.includes(metric.status));
  const focus = dashboard.drivers.map((driver) => ({
    location: driver.location,
    delta: driver.delta,
  }));

  if (assessed.length === 0) {
    return {
      tone: 'unknown',
      heading: 'Not enough history yet',
      supporting: `We need ${Math.max(4, dashboard.period.baseline_weeks)} comparable weeks before we can say what normal looks like here.`,
      focus: [],
    };
  }

  if (out.length === 0) {
    return {
      tone: 'normal',
      heading: thisWeek ? `All good this week${soFar}` : 'All good last week',
      supporting: `All ${assessed.length} measures are inside this account's usual range.`,
      focus: [],
    };
  }

  const names = out.map((metric) => metric.label.toLowerCase());
  const first = names[0] ?? '';
  const listed =
    names.length === 1 ? first : `${names.slice(0, -1).join(', ')} and ${names.at(-1)}`;
  const capitalised = listed.charAt(0).toUpperCase() + listed.slice(1);
  return {
    tone: 'attention',
    heading: `${out.length} of ${assessed.length} measures ${
      out.length === 1 ? 'is' : 'are'
    } unusual${soFar}`,
    supporting: `${capitalised} ${out.length === 1 ? 'is' : 'are'} outside the usual range.`,
    focus,
  };
}
