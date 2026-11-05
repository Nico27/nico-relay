import type { Metric } from '../types';
import {
  describeDelta,
  describeMultiple,
  formatMetricValue,
  statusLabel,
  usualRange,
} from '../format';
import { Sparkline } from './Sparkline';
import { StatusChip } from './StatusChip';

interface MetricCardProps {
  metric: Metric;
  periodLabel: string;
}

export function MetricCard({ metric, periodLabel }: MetricCardProps) {
  const range = usualRange(metric);
  const percent = metric.unit === 'percent';
  const comparable = metric.low !== null && metric.high !== null;
  const multiple = metric.status === 'above_typical' ? describeMultiple(metric.ratio) : null;

  return (
    <article className={`card card--${metric.status}`} aria-labelledby={`metric-${metric.key}`}>
      <header className="card__head">
        <h3 className="card__label" id={`metric-${metric.key}`}>
          {metric.label}
        </h3>
        <StatusChip status={metric.status} compact />
      </header>

      <p className="card__value">{formatMetricValue(metric)}</p>

      {range ? (
        <p className="card__range">{range}</p>
      ) : (
        <p className="card__range card__range--muted">
          {metric.status === 'not_enough_data'
            ? 'Too few to judge this period'
            : 'No comparable history yet'}
        </p>
      )}

      <Sparkline
        series={metric.series}
        low={metric.low}
        high={metric.high}
        percent={percent}
        label={`${metric.label} by week, ${periodLabel}`}
      />

      <footer className="card__foot">
        {comparable ? (
          <span>
            {describeDelta(metric)}
            {multiple ? <span className="card__ratio"> · {multiple}</span> : null}
          </span>
        ) : (
          <span className="card__quiet">
            {metric.status === 'not_enough_data'
              ? `${metric.denominator ?? 0} counted — we need 5 before a rate means anything.`
              : `${Math.max(0, metric.series.length - 1)} weeks of history — we need 4 to compare.`}
          </span>
        )}
      </footer>

      {metric.note ? <p className="card__note">{metric.note}</p> : null}
      <span className="visually-hidden">{statusLabel(metric.status)}</span>
    </article>
  );
}
