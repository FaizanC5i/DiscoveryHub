/**
 * HTTP client for the FastAPI backend.
 *
 * Responsibilities:
 *   1. Send JSON requests with the session cookies attached.
 *   2. Turn every error response into an ApiError with a stable `code`, so
 *      components branch on codes such as "ACCOUNT_NOT_FOUND", not on text.
 *   3. On a 401 in the browser, refresh the session once and retry the request.
 *      If the refresh fails, send the user to the login page.
 *
 * Analogy: a courier with an access card. When the card stops working, the
 * courier does not give up at once. They go to the front desk, trade the old
 * card for a new one (the refresh), and try the door again. Only if the desk
 * refuses do they send the visitor back to reception (login).
 *
 * Server components also use this module. They pass the incoming cookie header
 * explicitly, because server code has no browser cookie jar. A server
 * component cannot write cookies, so on the server we never attempt a refresh.
 * The Next.js proxy does that instead (see proxy.ts).
 */

import { ROUTES } from "@/lib/constants";
import { API_PATHS } from "./endpoints";

export const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

/** Paths where a 401 means "wrong credentials", not "session expired". Never refresh on these. */
const PATHS_WITHOUT_REFRESH = new Set<string>([
  API_PATHS.auth.login,
  API_PATHS.auth.signUp,
  API_PATHS.auth.refresh,
  API_PATHS.auth.logout,
  API_PATHS.auth.forgotPassword,
  API_PATHS.auth.resetPassword,
]);

export class ApiError extends Error {
  /** HTTP status, or 0 when the server could not be reached at all. */
  readonly status: number;
  /** Stable machine-readable code from the backend, e.g. "INVALID_CREDENTIALS". */
  readonly code: string;

  constructor(message: string, status: number, code: string) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.code = code;
  }
}

export function isApiError(error: unknown, code?: string): error is ApiError {
  return error instanceof ApiError && (code === undefined || error.code === code);
}

export interface ApiRequestInit extends RequestInit {
  /**
   * Set true to skip the automatic refresh-and-retry. The server side always
   * skips it. Auth paths in PATHS_WITHOUT_REFRESH skip it too.
   */
  skipAuthRefresh?: boolean;
}

/**
 * Call the backend and parse the JSON response.
 *
 * Usage: apiRequest<UserResponse>(API_PATHS.auth.me)
 */
export async function apiRequest<T>(path: string, init: ApiRequestInit = {}): Promise<T> {
  const { skipAuthRefresh = false, ...requestInit } = init;
  const canRefresh = isBrowser() && !skipAuthRefresh && !PATHS_WITHOUT_REFRESH.has(path);

  const first = await sendRequest(path, requestInit);
  if (first.status !== 401 || !canRefresh) {
    return parseResponse<T>(first);
  }

  // The access token has probably expired. Refresh once, then retry the original request.
  const refreshed = await refreshSession();
  if (!refreshed) {
    redirectToLogin();
    throw new ApiError("Your session has expired. Please sign in again.", 401, "SESSION_EXPIRED");
  }

  return parseResponse<T>(await sendRequest(path, requestInit));
}

/*
 * Refresh deduplication.
 *
 * Several components can get a 401 at the same moment. Without this, each one
 * would call /refresh. The first rotation would then invalidate the refresh token
 * the others are still holding, and the backend would read it as reuse. Sharing
 * one in-flight promise means one refresh serves all of them.
 */
let inFlightRefresh: Promise<boolean> | null = null;

function refreshSession(): Promise<boolean> {
  if (!inFlightRefresh) {
    inFlightRefresh = sendRequest(API_PATHS.auth.refresh, { method: "POST" })
      .then((response) => response.ok)
      .catch(() => false)
      .finally(() => {
        inFlightRefresh = null;
      });
  }
  return inFlightRefresh;
}

/** Send the user to sign in. Skips the redirect if they are already on the login page. */
function redirectToLogin(): void {
  if (window.location.pathname !== ROUTES.login) {
    window.location.assign(ROUTES.login);
  }
}

async function sendRequest(path: string, init: RequestInit): Promise<Response> {
  const headers = new Headers(init.headers);
  if (init.body !== undefined && !headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json");
  }

  try {
    return await fetch(`${API_BASE_URL}${path}`, {
      ...init,
      headers,
      // Send cookies to the API even though it is on another port.
      // Cookies are shared between localhost ports, so the browser treats the
      // API and the Next.js app as the same site and attaches them.
      credentials: "include",
    });
  } catch {
    // fetch() only throws when the network fails or the server is not running.
    throw new ApiError("Cannot reach the server. Please try again.", 0, "NETWORK_ERROR");
  }
}

async function parseResponse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    throw await toApiError(response);
  }
  if (response.status === 204) {
    return undefined as T;
  }
  return (await response.json()) as T;
}

/**
 * Read the backend's error body. Three shapes are possible:
 *   - ours:       { "detail": { "code": "...", "message": "..." } }
 *   - FastAPI:    { "detail": [{ "msg": "...", ... }] }   (validation, 422)
 *   - anything else: fall back to a generic message.
 */
async function toApiError(response: Response): Promise<ApiError> {
  const fallback = `Request failed with status ${response.status}`;
  let body: { detail?: unknown } = {};
  try {
    body = (await response.json()) as { detail?: unknown };
  } catch {
    return new ApiError(fallback, response.status, "UNKNOWN");
  }

  const { detail } = body;

  if (detail && typeof detail === "object" && !Array.isArray(detail)) {
    const { code, message } = detail as { code?: unknown; message?: unknown };
    return new ApiError(
      typeof message === "string" ? message : fallback,
      response.status,
      typeof code === "string" ? code : "UNKNOWN",
    );
  }

  if (Array.isArray(detail) && detail.length > 0) {
    const first = detail[0] as { msg?: unknown };
    if (typeof first.msg === "string") {
      // Pydantic prefixes validator messages with "Value error, ". Remove it for display.
      return new ApiError(first.msg.replace(/^Value error, /, ""), response.status, "VALIDATION_ERROR");
    }
  }

  return new ApiError(fallback, response.status, "UNKNOWN");
}

function isBrowser(): boolean {
  return typeof window !== "undefined";
}
