import type { AccountSummary } from '../types';

export function LoadingState({ label = 'Loading activity' }: { label?: string }) {
  return (
    <div className="state" role="status" aria-live="polite" aria-busy="true">
      <span className="visually-hidden">{label}</span>
      <div className="skeleton skeleton--hero" />
      <div className="skeleton-grid">
        {[0, 1, 2, 3, 4, 5].map((index) => (
          <div className="skeleton skeleton--card" key={index} />
        ))}
      </div>
      <div className="skeleton skeleton--table" />
    </div>
  );
}

export function ErrorState({
  message,
  onRetry,
}: {
  message: string;
  onRetry: () => void;
}) {
  return (
    <div className="state state--error" role="alert">
      <h2>We couldn&apos;t load this dashboard</h2>
      <p>{message}</p>
      <button type="button" className="button" onClick={onRetry}>
        Try again
      </button>
    </div>
  );
}

export function EmptyState({ account }: { account: AccountSummary }) {
  return (
    <div className="state state--empty">
      <h2>No activity yet for {account.name}</h2>
      <p>
        Nothing has been recorded for this account, so there is nothing to compare against. As soon
        as calls, leads or appointments arrive, this page will show whether a week is typical for
        you — and which site moved if it isn&apos;t.
      </p>
      <p className="state__meta">
        {account.locations.length === 0
          ? 'No locations have reported yet.'
          : `${account.locations.length} locations are connected.`}
      </p>
    </div>
  );
}
