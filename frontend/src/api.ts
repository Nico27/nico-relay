import type { AccountsResponse, DashboardResponse } from './types';

const BASE = import.meta.env.VITE_API_BASE ?? '';

export class ApiError extends Error {
  readonly status: number;

  constructor(message: string, status: number) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
  }
}

async function request<T>(path: string): Promise<T> {
  let response: Response;
  try {
    response = await fetch(`${BASE}${path}`, { headers: { accept: 'application/json' } });
  } catch {
    throw new ApiError('Could not reach the dashboard service.', 0);
  }
  if (!response.ok) {
    let detail = `Request failed (${response.status}).`;
    try {
      const body = (await response.json()) as { detail?: unknown };
      if (typeof body.detail === 'string') detail = body.detail;
    } catch {
      // keep the generic message
    }
    throw new ApiError(detail, response.status);
  }
  return (await response.json()) as T;
}

export function fetchAccounts(): Promise<AccountsResponse> {
  return request<AccountsResponse>('/api/v1/accounts');
}

export function fetchDashboard(
  accountId: number,
  opts: { asOf?: string } = {},
): Promise<DashboardResponse> {
  const query = opts.asOf ? `?as_of=${encodeURIComponent(opts.asOf)}` : '';
  return request<DashboardResponse>(`/api/v1/accounts/${accountId}/dashboard${query}`);
}
