import { render, screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';

import { App } from './App';
import { accountsResponse, metroDashboard, quietHarborDashboard } from './__fixtures__/dashboard';

const fetchMock = vi.fn();

function jsonResponse(body: unknown, status = 200): Promise<Response> {
  return Promise.resolve(
    new Response(JSON.stringify(body), {
      status,
      headers: { 'content-type': 'application/json' },
    }),
  );
}

function routeDashboard(payload: unknown) {
  fetchMock.mockImplementation((input: RequestInfo | URL) => {
    const url = String(input);
    if (url.includes('/api/v1/accounts/') && url.includes('/dashboard')) {
      return jsonResponse(payload);
    }
    if (url.includes('/api/v1/accounts')) {
      return jsonResponse(accountsResponse);
    }
    return jsonResponse({ detail: 'not found' }, 404);
  });
}

beforeEach(() => {
  fetchMock.mockReset();
  vi.stubGlobal('fetch', fetchMock);
  window.history.replaceState({}, '', '/');
});

afterEach(() => {
  vi.unstubAllGlobals();
});

describe('App', () => {
  it('renders the verdict, six metric cards and the location rows', async () => {
    routeDashboard(metroDashboard);
    render(<App />);

    expect(await screen.findByRole('heading', { name: /measures are unusual/i })).toBeVisible();
    expect(screen.getByText(/Most of the change came from/)).toBeInTheDocument();
    // "why" is answered on the page, not by a manager
    expect(screen.getByText('Start here:')).toBeInTheDocument();

    const metrics = screen.getAllByRole('article');
    expect(metrics).toHaveLength(6);

    const table = screen.getByRole('table');
    expect(within(table).getAllByRole('row')).toHaveLength(
      metroDashboard.locations.length + 1,
    );

    // staleness is disclosed, never implied
    expect(screen.getByText(/Data through/)).toHaveTextContent(/days ago/);
    expect(screen.getByText('About this data')).toBeInTheDocument();
  });

  it('marks the headline when it speaks about the open week', async () => {
    routeDashboard({
      ...metroDashboard,
      headline: {
        ...metroDashboard.headline,
        basis: 'this_week',
        status: 'above_typical',
        title: 'This week is busier than usual so far',
      },
      // the open week is what the headline is about, so its metrics must be what
      // drives the verdict
      in_progress: metroDashboard.in_progress
        ? {
            ...metroDashboard.in_progress,
            metrics: metroDashboard.in_progress.metrics.map((metric) => ({
              ...metric,
              status: 'above_typical' as const,
            })),
          }
        : null,
    });
    render(<App />);
    expect(
      await screen.findByRole('heading', { name: /unusual so far/i }),
    ).toBeInTheDocument();
    expect(screen.getByText(/This week so far/, { selector: '.hero__period' })).toBeInTheDocument();
  });

  it('renders an empty state instead of a zero baseline', async () => {
    routeDashboard(quietHarborDashboard);
    render(<App />);
    expect(await screen.findByRole('heading', { name: /No activity yet/ })).toBeInTheDocument();
    expect(screen.queryByRole('article')).not.toBeInTheDocument();
    expect(screen.queryByText(/Below typical/)).not.toBeInTheDocument();
  });

  it('shows an error with a working retry', async () => {
    fetchMock.mockImplementationOnce(() => jsonResponse(accountsResponse));
    fetchMock.mockImplementationOnce(() =>
      jsonResponse({ detail: 'No activity data available yet' }, 503),
    );
    render(<App />);

    expect(await screen.findByRole('alert')).toHaveTextContent(
      /No activity data available yet/,
    );

    routeDashboard(metroDashboard);
    await userEvent.click(screen.getByRole('button', { name: /try again/i }));

    expect(
      await screen.findByRole('heading', { name: /measures are unusual/i }),
    ).toBeInTheDocument();
  });

  it('switches account, refetches and keeps the URL in sync', async () => {
    routeDashboard(metroDashboard);
    render(<App />);
    await screen.findByRole('heading', { name: /measures are unusual/i });

    const first = accountsResponse.accounts[0]!;
    expect(window.location.search).toBe(`?account=${first.id}`);

    const picker = screen.getByLabelText('Account') as HTMLSelectElement;
    const other = accountsResponse.accounts[1]!;
    await userEvent.selectOptions(picker, String(other.id));

    await waitFor(() => {
      expect(window.location.search).toBe(`?account=${other.id}`);
    });
    expect(fetchMock).toHaveBeenCalledWith(
      expect.stringContaining(`/api/v1/accounts/${other.id}/dashboard`),
      expect.anything(),
    );
  });

  it('restores the account from the URL', async () => {
    window.history.replaceState({}, '', '/?account=20');
    routeDashboard(quietHarborDashboard);
    render(<App />);
    expect(await screen.findByRole('heading', { name: /No activity yet/ })).toBeInTheDocument();
    expect(fetchMock).toHaveBeenCalledWith(
      expect.stringContaining('/api/v1/accounts/20/dashboard'),
      expect.anything(),
    );
  });
});
