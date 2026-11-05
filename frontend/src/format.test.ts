import {
  describeDelta,
  describeMultiple,
  formatDateLong,
  formatDay,
  formatDelta,
  formatNumber,
  formatPercent,
  formatRange,
  formatRatio,
  formatTypical,
  statusGlyph,
  statusLabel,
  statusTone,
  summarise,
  usualRange,
} from './format';
import type { Metric, MetricStatus } from './types';
import { metroDashboard, quietHarborDashboard } from './__fixtures__/dashboard';

function metric(partial: Partial<Metric>): Metric {
  return {
    key: 'activity',
    label: 'Activity',
    unit: 'events',
    kind: 'volume',
    status: 'within_typical',
    current: 70,
    typical: 70,
    low: 63,
    high: 77,
    delta: 0,
    ratio: 1,
    numerator: 70,
    denominator: null,
    series: [],
    note: null,
    ...partial,
  };
}

describe('number formatting', () => {
  it('formats counts with separators and no decimals', () => {
    expect(formatNumber(1223)).toBe('1,223');
    expect(formatNumber(0)).toBe('0');
    expect(formatNumber(null)).toBe('—');
  });

  it('formats rates with one decimal', () => {
    expect(formatPercent(22.34)).toBe('22.3%');
    expect(formatPercent(0)).toBe('0.0%');
    expect(formatPercent(null)).toBe('—');
  });

  it('signs deltas with a real minus sign', () => {
    expect(formatDelta(62)).toBe('+62');
    expect(formatDelta(-62)).toBe('\u221262');
    expect(formatDelta(0)).toBe('0');
    expect(formatDelta(null)).toBe('—');
  });

  it('formats ratios', () => {
    expect(formatRatio(13.33)).toBe('13.3×');
    expect(formatRatio(3)).toBe('3×');
    expect(formatRatio(null)).toBe('—');
  });

  it('formats day labels without shifting across timezones', () => {
    expect(formatDay('2026-07-27')).toBe('Jul 27');
    expect(formatDateLong('2026-07-27')).toBe('Jul 27, 2026');
  });
});

describe('range formatting', () => {
  it('renders volume ranges without percent signs', () => {
    expect(formatRange(metric({}))).toBe('63–77');
  });

  it('renders rate ranges in percentage points', () => {
    const rate = metric({
      key: 'missed_call_rate',
      label: 'Missed-call rate',
      unit: 'percent',
      kind: 'rate',
      current: 22.3,
      typical: 13,
      low: 12,
      high: 15,
    });
    expect(formatRange(rate)).toBe('12.0–15.0%');
    expect(formatTypical(rate)).toBe('13.0%');
  });

  it('degrades to a dash without a baseline', () => {
    expect(formatRange(metric({ low: null, high: null }))).toBe('—');
    expect(formatTypical(metric({ typical: null }))).toBeNull();
  });
});

describe('status vocabulary', () => {
  const statuses: MetricStatus[] = [
    'above_typical',
    'within_typical',
    'below_typical',
    'insufficient_history',
    'not_enough_data',
    'no_activity',
  ];

  it('labels every status in plain language', () => {
    expect(statuses.map(statusLabel)).toEqual([
      'Higher than usual',
      'Normal',
      'Lower than usual',
      'Not enough history yet',
      'Not enough data yet',
      'No activity',
    ]);
  });

  it('gives every status a glyph, never a bare colour', () => {
    for (const status of statuses) {
      expect(statusGlyph(status).length).toBeGreaterThan(0);
    }
  });

  it('maps direction, not good or bad, to a tone', () => {
    expect(statusTone('above_typical')).toBe('above');
    expect(statusTone('below_typical')).toBe('below');
    expect(statusTone('within_typical')).toBe('normal');
    expect(statusTone('insufficient_history')).toBe('muted');
  });
});

describe('describeDelta', () => {
  it('states the difference in everyday words', () => {
    expect(describeDelta(metric({ delta: 12, typical: 70 }))).toBe('12 more than usual');
    expect(describeDelta(metric({ delta: -12, typical: 70 }))).toBe('12 fewer than usual');
    expect(describeDelta(metric({ delta: 0 }))).toBe('right at the usual level');
  });

  it('says there is nothing to compare with instead of inventing a baseline', () => {
    expect(describeDelta(metric({ delta: null, typical: null, low: null, high: null }))).toBe(
      'Nothing to compare with yet',
    );
  });
});

describe('usual wording', () => {
  it('turns a range into a sentence', () => {
    expect(usualRange(metric({}))).toBe('usually 63–77');
    expect(usualRange(metric({ low: null, high: null }))).toBeNull();
  });

  it('rounds multipliers instead of implying precision', () => {
    expect(describeMultiple(13.33)).toBe('about 13× a normal week');
    expect(describeMultiple(3.75)).toBe('about 3.8× a normal week');
    expect(describeMultiple(null)).toBeNull();
  });
});

describe('summarise', () => {
  it('answers "is all good" first when nothing is out of range', () => {
    const allNormal = {
      ...metroDashboard,
      headline: { ...metroDashboard.headline, basis: 'last_week' as const },
      metrics: metroDashboard.metrics.map((m) => ({
        ...m,
        status: 'within_typical' as const,
      })),
      drivers: [],
    };
    expect(summarise(allNormal)).toMatchObject({
      tone: 'normal',
      heading: 'All good last week',
    });
  });

  it('counts only the measures it could actually judge', () => {
    const verdict = summarise(metroDashboard);
    expect(verdict.tone).toBe('attention');
    expect(verdict.heading).toMatch(/^\d of \d measures are unusual/);
    expect(verdict.supporting).toContain('outside the usual range');
    expect(verdict.focus.length).toBeGreaterThan(0);
  });

  it('refuses to declare a verdict without history', () => {
    const verdict = summarise(quietHarborDashboard);
    expect(verdict.tone).toBe('unknown');
    expect(verdict.heading).toBe('No activity yet');
  });

  it('follows the window the headline talks about', () => {
    const thisWeek = {
      ...metroDashboard,
      headline: { ...metroDashboard.headline, basis: 'this_week' as const },
      metrics: metroDashboard.metrics.map((m) => ({ ...m, status: 'within_typical' as const })),
      in_progress: metroDashboard.in_progress
        ? {
            ...metroDashboard.in_progress,
            metrics: metroDashboard.in_progress.metrics.map((m) => ({
              ...m,
              status: 'above_typical' as const,
            })),
          }
        : null,
    };
    const verdict = summarise(thisWeek);
    expect(verdict.tone).toBe('attention');
    expect(verdict.heading).toContain('so far');
  });
});
