import type { Location, MetricStatus } from '../types';
import {
  formatDelta,
  formatNumber,
  formatPercent,
  formatRange,
  statusGlyph,
  statusLabel,
  statusTone,
} from '../format';

interface LocationTableProps {
  locations: Location[];
  periodLabel: string;
}

function Delta({ value, status }: { value: number | null; status: MetricStatus }) {
  if (value === null) return <span className="delta delta--muted">—</span>;
  const rounded = Math.round(value);
  if (rounded === 0) return <span className="delta delta--muted">0</span>;
  const notable = status === 'above_typical' || status === 'below_typical';
  return (
    <span className={`delta delta--${statusTone(status)}`} aria-label={statusLabel(status)}>
      {notable ? (
        <span className="delta__glyph" aria-hidden="true">
          {statusGlyph(status)}{' '}
        </span>
      ) : null}
      {formatDelta(value)}
    </span>
  );
}

function Rate({ value, status }: { value: number | null; status: MetricStatus }) {
  if (value === null) {
    return (
      <span className="num num--muted" aria-label="Not enough data">
        —
      </span>
    );
  }
  const notable = status === 'above_typical' || status === 'below_typical';
  const glyph = notable ? statusGlyph(status) : null;
  return (
    <span
      className={notable ? `num num--${statusTone(status)}` : 'num'}
      aria-label={`${formatPercent(value)} (${statusLabel(status)})`}
    >
      {glyph ? (
        <span className="num__glyph" aria-hidden="true">
          {glyph}{' '}
        </span>
      ) : null}
      {formatPercent(value)}
    </span>
  );
}

export function LocationTable({ locations, periodLabel }: LocationTableProps) {
  if (locations.length === 0) return null;

  return (
    <section className="panel" aria-labelledby="locations-title">
      <header className="panel__head">
        <h2 id="locations-title">By location</h2>
        <p className="panel__hint">
          {periodLabel} · biggest change first, so the site to check is at the top
        </p>
      </header>

      <div className="table-scroll" tabIndex={0} role="region" aria-label="Activity by location">
        <table className="table">
          <caption className="visually-hidden">
            Activity by location for {periodLabel}, compared with each location&apos;s own usual
            range.
          </caption>
          <thead>
            <tr>
              <th scope="col">Site</th>
              <th scope="col" className="is-numeric">
                Activity
              </th>
              <th scope="col" className="is-numeric">
                vs usual
              </th>
              <th scope="col" className="is-numeric">
                Usual range
              </th>
              <th scope="col" className="is-numeric">
                Calls
              </th>
              <th scope="col" className="is-numeric">
                Missed
              </th>
              <th scope="col" className="is-numeric">
                Leads
              </th>
              <th scope="col" className="is-numeric">
                Appts
              </th>
              <th scope="col" className="is-numeric">
                No-shows
              </th>
            </tr>
          </thead>
          <tbody>
            {locations.map((row) => (
              <tr key={row.location} className={row.note ? 'row--flagged' : undefined}>
                <th scope="row">
                  {row.location}
                  {row.note ? <span className="row__note">{row.note}</span> : null}
                </th>
                <td className="is-numeric">
                  <strong className="num">{formatNumber(row.current)}</strong>
                </td>
                <td className="is-numeric">
                  <Delta value={row.delta} status={row.status} />
                </td>
                <td className="is-numeric num num--muted">
                  {row.low === null || row.high === null
                    ? '—'
                    : formatRange({ unit: 'events', low: row.low, high: row.high })}
                </td>
                <td className="is-numeric num">{formatNumber(row.calls)}</td>
                <td className="is-numeric">
                  <Rate value={row.missed_rate} status={row.missed_rate_status} />
                </td>
                <td className="is-numeric num">{formatNumber(row.leads)}</td>
                <td className="is-numeric num">{formatNumber(row.appointments)}</td>
                <td className="is-numeric">
                  {/* The contract carries the value but not a verdict per location. */}
                  <span className={row.no_show_rate === null ? 'num num--muted' : 'num'}>
                    {formatPercent(row.no_show_rate)}
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}
