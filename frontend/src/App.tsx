import { useCallback, useEffect, useState } from 'react';

import { ApiError, fetchAccounts, fetchDashboard } from './api';
import type { AccountSummary, DashboardResponse } from './types';
import { AccountPicker } from './components/AccountPicker';
import { DataQualityNotes } from './components/DataQualityNotes';
import { Headline } from './components/Headline';
import { LocationTable } from './components/LocationTable';
import { MetricCard } from './components/MetricCard';
import { EmptyState, ErrorState, LoadingState } from './components/States';
import { WeekSoFar } from './components/WeekSoFar';

function readAccountFromUrl(): number | null {
  if (typeof window === 'undefined') return null;
  const raw = new URLSearchParams(window.location.search).get('account');
  if (!raw) return null;
  const parsed = Number(raw);
  return Number.isInteger(parsed) && parsed > 0 ? parsed : null;
}

function readAsOfFromUrl(): string | undefined {
  if (typeof window === 'undefined') return undefined;
  const raw = new URLSearchParams(window.location.search).get('as_of');
  return raw && /^\d{4}-\d{2}-\d{2}$/.test(raw) ? raw : undefined;
}

function writeAccountToUrl(id: number): void {
  if (typeof window === 'undefined') return;
  const url = new URL(window.location.href);
  url.searchParams.set('account', String(id));
  window.history.replaceState({}, '', url);
}

export function App() {
  const [accounts, setAccounts] = useState<AccountSummary[] | null>(null);
  const [selectedId, setSelectedId] = useState<number | null>(readAccountFromUrl);
  const [dashboard, setDashboard] = useState<DashboardResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [reloadToken, setReloadToken] = useState(0);
  // Support / demo override: `?as_of=YYYY-MM-DD` re-anchors the analysis without
  // changing data. Documented in README; not part of the customer-facing UI.
  const [asOf] = useState<string | undefined>(readAsOfFromUrl);

  const retry = useCallback(() => setReloadToken((token) => token + 1), []);

  useEffect(() => {
    let cancelled = false;
    fetchAccounts()
      .then((response) => {
        if (cancelled) return;
        setAccounts(response.accounts);
        setSelectedId((current) => {
          if (current !== null && response.accounts.some((a) => a.id === current)) {
            return current;
          }
          return response.accounts[0]?.id ?? null;
        });
      })
      .catch((cause: unknown) => {
        if (cancelled) return;
        setError(cause instanceof ApiError ? cause.message : 'Unexpected error.');
        setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [reloadToken]);

  useEffect(() => {
    if (selectedId === null) return;
    let cancelled = false;
    setLoading(true);
    setError(null);
    fetchDashboard(selectedId, { asOf })
      .then((response) => {
        if (cancelled) return;
        setDashboard(response);
        setLoading(false);
        writeAccountToUrl(selectedId);
      })
      .catch((cause: unknown) => {
        if (cancelled) return;
        setDashboard(null);
        setError(cause instanceof ApiError ? cause.message : 'Unexpected error.');
        setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [selectedId, reloadToken, asOf]);

  const selectedAccount =
    accounts?.find((account) => account.id === selectedId) ?? accounts?.[0] ?? null;

  return (
    <div className="app">
      <header className="topbar">
        <div className="topbar__brand">
          <span className="topbar__mark" aria-hidden="true" />
          <span className="topbar__name">Relay</span>
          <span className="topbar__divider" aria-hidden="true" />
          <span className="topbar__tagline">Is this normal for us?</span>
        </div>
        {accounts && accounts.length > 0 && selectedAccount ? (
          <AccountPicker
            accounts={accounts}
            selectedId={selectedAccount.id}
            onChange={(id) => {
              setSelectedId(id);
              writeAccountToUrl(id);
            }}
          />
        ) : null}
      </header>

      <main className="main">
        {error ? <ErrorState message={error} onRetry={retry} /> : null}

        {!error && loading ? <LoadingState /> : null}

        {!error && !loading && dashboard && dashboard.empty && selectedAccount ? (
          <EmptyState account={selectedAccount} />
        ) : null}

        {!error && !loading && dashboard && !dashboard.empty ? (
          <>
            <Headline dashboard={dashboard} />

            <section className="metrics" aria-label="Metrics for this period">
              {dashboard.metrics.map((metric) => (
                <MetricCard key={metric.key} metric={metric} periodLabel={dashboard.period.label} />
              ))}
            </section>

            <WeekSoFar inProgress={dashboard.in_progress} />

            <LocationTable
              locations={dashboard.locations}
              periodLabel={dashboard.period.label}
            />

            <DataQualityNotes notes={dashboard.data_quality} />
          </>
        ) : null}
      </main>

      <footer className="footer">
        <span>
          Baseline: your own previous {dashboard?.period.baseline_weeks ?? 8} weeks, matched by
          weekday.
        </span>
        <span className="footer__meta">DASH-247</span>
      </footer>
    </div>
  );
}
