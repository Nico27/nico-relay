import type { InProgress } from '../types';
import { formatMetricValue, statusGlyph, statusLabel, statusTone } from '../format';

interface WeekSoFarProps {
  inProgress: InProgress | null;
}

export function WeekSoFar({ inProgress }: WeekSoFarProps) {
  if (!inProgress) return null;

  const allUnknown = inProgress.metrics.every(
    (metric) => metric.status === 'insufficient_history',
  );

  return (
    <section className="panel panel--tight" aria-labelledby="week-so-far-title">
      <header className="panel__head">
        <h2 id="week-so-far-title">{inProgress.label}</h2>
        <p className="panel__hint">
          {allUnknown
            ? 'Not enough days yet to compare with the same days in earlier weeks.'
            : 'Compared with the same weekdays in earlier weeks, so a short week is never measured against a full one.'}
        </p>
      </header>

      <ul className="strip">
        {inProgress.metrics.map((metric) => (
          <li key={metric.key} className={`strip__item strip--${statusTone(metric.status)}`}>
            <span className="strip__label">{metric.label}</span>
            <span className="strip__value">{formatMetricValue(metric)}</span>
            <span
              className="strip__status"
              aria-label={`Status: ${statusLabel(metric.status)}`}
            >
              <span aria-hidden="true">{statusGlyph(metric.status)}</span>
              <span className="strip__status-text">{statusLabel(metric.status)}</span>
            </span>
          </li>
        ))}
      </ul>
    </section>
  );
}
