import type { components } from "./schema";
type S = components["schemas"];
export type Measure = S["MeasureView"];
export type Profile = S["BusinessProfile-Input"];
export type Match = S["MatchView"];
export type Plan = S["PlanView"];
export type Session = S["SessionView"];
export type Check = S["CheckView"];
export type ProfileQuestion = S["ProfileQuestion"];
export let csrf = "";
export function setSession(session: Session | null) {
  csrf = session?.csrf || "";
}
type ErrorBody = { detail?: unknown; errors?: { field: string; message: string }[] };
export class ApiError extends Error {
  constructor(
    message: string,
    public status: number,
  ) {
    super(message);
  }
}
export async function api<T>(path: string, method = "GET", body?: unknown): Promise<T> {
  const response = await fetch("/api" + path, {
    method,
    credentials: "same-origin",
    headers: { "Content-Type": "application/json", "X-App-Request": "1", "X-CSRF-Token": csrf },
    body: body === undefined ? undefined : JSON.stringify(body),
  });
  // Прокси (429, 502, 413) отвечает HTML, а не JSON.
  const data: unknown = await response.json().catch(() => null);
  if (!response.ok) {
    const error = data as ErrorBody | null;
    const fields = error?.errors?.map((e) => `${e.field}: ${e.message}`).join("; ");
    const detail =
      (typeof error?.detail === "string" && error.detail) ||
      (response.status === 429
        ? "Слишком много запросов. Подождите минуту и повторите"
        : response.status >= 500
          ? "Сервер временно недоступен. Повторите позже"
          : "Не удалось выполнить запрос");
    throw new ApiError(detail + (fields ? ": " + fields : ""), response.status);
  }
  if (data === null) throw new ApiError("Сервер вернул некорректный ответ", response.status);
  return data as T;
}
