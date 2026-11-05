import type { DashboardResponse } from '../types';
import { formatDateLong, formatDelta, summarise } from '../format';
import { StatusChip } from './StatusChip';

interface HeadlineProps {
  dashboard: DashboardResponse;
}

export function Headline({ dashboard }: HeadlineProps) {
  const { headline, period, staleness_days: staleness, data_through: dataThrough } = dashboard;
  const thisWeek = headline.basis === 'this_week';
  const verdict = summarise(dashboard);

  return (
    <section className={`hero hero--${verdict.tone}`} aria-labelledby="hero-title">
      <div className="hero__meta">
        <StatusChip status={headline.status} />
        <span className="hero__period">
          {thisWeek ? 'This week so far' : `Last complete week · ${period.label}`}
        </span>
        {dashboard.as_of_source === 'requested' ? (
          <span className="hero__asof" title="Analysis horizon supplied in the URL">
            Custom date
          </span>
        ) : null}
        {staleness > 0 ? (
          <span className="hero__freshness">
            Data through {formatDateLong(dataThrough)} · {staleness} days ago
          </span>
        ) : (
          <span className="hero__freshness">Data through {formatDateLong(dataThrough)}</span>
        )}
      </div>

      <h1 className="hero__title" id="hero-title" aria-live="polite">
        {verdict.heading}
      </h1>

      {verdict.supporting ? <p className="hero__supporting">{verdict.supporting}</p> : null}

      <p className="hero__narrative">{dashboard.narrative}</p>

      {verdict.focus.length > 0 ? (
        <p className="hero__focus">
          <span className="hero__focus-label">Start here:</span>
          {verdict.focus.map((item) => (
            <span className="hero__focus-chip" key={item.location}>
              {item.location}
              <span className="hero__focus-delta">{formatDelta(item.delta)}</span>
            </span>
          ))}
        </p>
      ) : null}

      <p className="hero__scope">
        {thisWeek
          ? `Judged against the same days in the previous ${period.baseline_weeks} weeks. The last complete week (${period.label}) is below.`
          : `Judged against the same weekdays in the previous ${period.baseline_weeks} weeks.`}
      </p>
    </section>
  );
}
