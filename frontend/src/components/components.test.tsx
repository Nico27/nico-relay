import { render, screen, within } from '@testing-library/react';

import { metroDashboard } from '../__fixtures__/dashboard';
import type { Metric, MetricStatus } from '../types';
import { LocationTable } from './LocationTable';
import { MetricCard } from './MetricCard';
import { StatusChip } from './StatusChip';
import { WeekSoFar } from './WeekSoFar';

function metric(partial: Partial<Metric>): Metric {
  const base = metroDashboard.metrics[0] as Metric;
  return { ...base, ...partial };
}

describe('StatusChip', () => {
  const cases: Array<[MetricStatus, string]> = [
    ['above_typical', 'Higher than usual'],
    ['within_typical', 'Normal'],
    ['below_typical', 'Lower than usual'],
    ['insufficient_history', 'Not enough history yet'],
    ['not_enough_data', 'Not enough data yet'],
    ['no_activity', 'No activity'],
  ];

  it.each(cases)('renders %s as "%s" with an aria label', (status, label) => {
    render(<StatusChip status={status} />);
    const chip = screen.getByLabelText(`Status: ${label}`);
    expect(chip).toBeInTheDocument();
    // text, not colour alone
    expect(within(chip).getByText(label)).toBeInTheDocument();
  });
});

describe('MetricCard', () => {
  it('shows the value, the usual range and a readable multiple', () => {
    const activity = metroDashboard.metrics[0] as Metric;
    render(<MetricCard metric={activity} periodLabel="Jun 1 – Jun 7" />);
    expect(screen.getByText('Activity')).toBeInTheDocument();
    expect(screen.getByText('880')).toBeInTheDocument();
    expect(screen.getByText('usually 46–93')).toBeInTheDocument();
    expect(screen.getByText(/about 13× a normal week/)).toBeInTheDocument();
    // the chart explains itself without a statistics lesson
    expect(screen.getByText(/weeks ago/)).toBeInTheDocument();
    expect(screen.getByText('usual range')).toBeInTheDocument();
    expect(screen.getByText('now')).toBeInTheDocument();
    // the period belongs to the page, not to every card
    expect(screen.queryByText(/Jun 1 – Jun 7/)).not.toBeInTheDocument();
  });

  it('describes the difference in everyday words', () => {
    render(<MetricCard metric={metric({ delta: 814 })} periodLabel="Jun 1 – Jun 7" />);
    expect(screen.getByText(/814 more than usual/)).toBeInTheDocument();
  });

  it('hides delta and ratio when there is not enough history', () => {
    render(
      <MetricCard
        metric={metric({
          status: 'insufficient_history',
          typical: null,
          low: null,
          high: null,
          delta: null,
          ratio: null,
        })}
        periodLabel="Jun 1 – Jun 7"
      />,
    );
    expect(screen.getByText(/No comparable history yet/)).toBeInTheDocument();
    expect(screen.queryByText(/more than usual/)).not.toBeInTheDocument();
    expect(screen.getByText(/weeks of history — we need 4 to compare/)).toBeInTheDocument();
  });

  it('explains a thin rate denominator instead of showing a number', () => {
    render(
      <MetricCard
        metric={metric({
          key: 'missed_call_rate',
          label: 'Missed-call rate',
          unit: 'percent',
          kind: 'rate',
          status: 'not_enough_data',
          current: null,
          typical: null,
          low: null,
          high: null,
          delta: null,
          ratio: null,
          denominator: 3,
        })}
        periodLabel="Jun 1 – Jun 7"
      />,
    );
    expect(screen.getByText(/we need 5 before a rate means anything/)).toBeInTheDocument();
  });

  it('renders the coverage note when the metric carries one', () => {
    render(
      <MetricCard
        metric={metric({ note: '3 of 120 calls had no outcome.' })}
        periodLabel="Jun 1 – Jun 7"
      />,
    );
    expect(screen.getByText('3 of 120 calls had no outcome.')).toBeInTheDocument();
  });
});

describe('LocationTable', () => {
  it('renders one row per location and marks notable deltas', () => {
    render(
      <LocationTable locations={metroDashboard.locations} periodLabel="Jun 1 – Jun 7" />,
    );
    const table = screen.getByRole('table');
    const rows = within(table).getAllByRole('row');
    expect(rows).toHaveLength(metroDashboard.locations.length + 1);
    expect(screen.getByText('Site N')).toBeInTheDocument();
    // direction is exposed as text, never as colour alone
    expect(screen.getAllByLabelText('Higher than usual').length).toBeGreaterThan(0);
    expect(screen.getAllByText(/^\+\d+/).length).toBeGreaterThan(0);
  });

  it('renders nothing when the account has no locations', () => {
    const { container } = render(<LocationTable locations={[]} periodLabel="Jun 1 – Jun 7" />);
    expect(container).toBeEmptyDOMElement();
  });
});

describe('WeekSoFar', () => {
  it('labels the strip and explains when it cannot judge yet', () => {
    const quiet = metroDashboard.in_progress;
    if (!quiet) throw new Error('fixture must carry an in_progress block');
    render(
      <WeekSoFar
        inProgress={{
          ...quiet,
          metrics: quiet.metrics.map((m) => ({ ...m, status: 'insufficient_history' as const })),
        }}
      />,
    );
    expect(screen.getByText(/This week so far/)).toBeInTheDocument();
    expect(screen.getByText(/Not enough days yet/)).toBeInTheDocument();
  });

  it('renders nothing when there is no open week', () => {
    const { container } = render(<WeekSoFar inProgress={null} />);
    expect(container).toBeEmptyDOMElement();
  });
});
