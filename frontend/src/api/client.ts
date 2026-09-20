import type { components } from './schema';
type S = components['schemas'];
export type Measure = S['MeasureView'];
export type Profile = S['BusinessProfile-Input'];
export type Match = S['MatchView'];
export type Plan = S['PlanView'];
export type Session = S['SessionView'];
export type Check = S['CheckView'];
export let csrf = '';
export function setSession(session: Session | null) { csrf = session?.csrf || ''; }
export class ApiError extends Error {
  constructor(message: string, public status: number) { super(message); }
}
export async function api<T>(path: string, method = 'GET', body?: unknown): Promise<T> {
  const response = await fetch('/api' + path, {method, credentials: 'same-origin',
    headers: {'Content-Type': 'application/json', 'X-App-Request': '1', 'X-CSRF-Token': csrf},
    body: body === undefined ? undefined : JSON.stringify(body)});
  const data = await response.json();
  if (!response.ok) {
    const fields = data.errors?.map((e: {field: string; message: string}) => `${e.field}: ${e.message}`).join('; ');
    throw new ApiError((data.detail || 'Не удалось выполнить запрос') + (fields ? ': ' + fields : ''), response.status);
  }
  return data as T;
}
