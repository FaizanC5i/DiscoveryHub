import { NextResponse, type NextRequest } from "next/server";
import { API_BASE_URL } from "@/lib/api/client";
import { API_PATHS } from "@/lib/api/endpoints";
import { AUTH_COOKIES, ROUTES } from "@/lib/constants";

/**
 * Proxy (formerly "middleware"): runs before a protected page renders.
 *
 * Analogy: a doorman who checks the wristband before the guest reaches the
 * room. If the wristband has expired but the guest still holds a valid booking
 * (refresh token), the doorman swaps in a new wristband at the desk and lets
 * them through. Only a guest with no valid booking is sent back to reception.
 *
 * Why here and not in the dashboard page? Server components cannot write
 * cookies, and a redirect from inside a page can flash the page's shell first.
 * The proxy runs before any rendering, can set cookies, and can send a clean
 * 307 redirect.
 *
 * This is an optimistic check. The access cookie's presence means "not yet
 * expired", because the browser deletes the cookie when its max-age passes. The
 * backend still verifies the token on every real request (see currentUser.ts), so
 * a token revoked early (for example by logout from another device) is caught there.
 */
export async function proxy(request: NextRequest) {
  // Access cookie still present: the browser has not yet dropped it, so let the request through.
  if (request.cookies.has(AUTH_COOKIES.access)) {
    return NextResponse.next();
  }

  // No access cookie and no refresh cookie: the visitor was never signed in, or has signed out.
  if (!request.cookies.has(AUTH_COOKIES.refresh)) {
    return redirectToLogin(request);
  }

  // Access expired, refresh present: try to renew silently.
  const refreshed = await refreshWithBackend(request);
  if (!refreshed) {
    const response = redirectToLogin(request);
    clearSessionCookies(response);
    return response;
  }

  // Pass the new cookies on two routes at once:
  //   1. Upstream, so the page render (cookies() in currentUser.ts) sees the new access token
  //      during this same request.
  //   2. Downstream, as Set-Cookie headers, so the browser stores the rotated tokens.
  const requestHeaders = new Headers(request.headers);
  requestHeaders.set("cookie", mergeCookieHeader(request.headers.get("cookie"), refreshed.cookies));

  const response = NextResponse.next({ request: { headers: requestHeaders } });
  for (const setCookie of refreshed.setCookieHeaders) {
    response.headers.append("set-cookie", setCookie);
  }
  return response;
}

interface RefreshResult {
  /** name -> new value, used to rewrite the upstream Cookie header. */
  cookies: Record<string, string>;
  /** Raw Set-Cookie strings from the backend, forwarded unchanged so attributes (HttpOnly, Max-Age) survive. */
  setCookieHeaders: string[];
}

async function refreshWithBackend(request: NextRequest): Promise<RefreshResult | null> {
  try {
    const backendResponse = await fetch(`${API_BASE_URL}${API_PATHS.auth.refresh}`, {
      method: "POST",
      headers: { cookie: request.headers.get("cookie") ?? "" },
      cache: "no-store",
      // Do not let a slow or hung backend freeze every protected page load.
      signal: AbortSignal.timeout(5000),
    });
    if (!backendResponse.ok) {
      return null;
    }

    const setCookieHeaders = backendResponse.headers.getSetCookie();
    const cookies: Record<string, string> = {};
    for (const header of setCookieHeaders) {
      const [pair] = header.split(";");
      const separator = pair.indexOf("=");
      if (separator > 0) {
        cookies[pair.slice(0, separator).trim()] = pair.slice(separator + 1);
      }
    }
    return { cookies, setCookieHeaders };
  } catch {
    // Backend down or timed out. Treat it as "not signed in" and send the user to login.
    return null;
  }
}

/**
 * Rewrite a Cookie header so the given names carry new values.
 * Other cookies are kept exactly as they were.
 */
function mergeCookieHeader(existing: string | null, updates: Record<string, string>): string {
  const merged = new Map<string, string>();
  for (const part of (existing ?? "").split(";")) {
    const separator = part.indexOf("=");
    if (separator > 0) {
      merged.set(part.slice(0, separator).trim(), part.slice(separator + 1).trim());
    }
  }
  for (const [name, value] of Object.entries(updates)) {
    merged.set(name, value);
  }
  return Array.from(merged, ([name, value]) => `${name}=${value}`).join("; ");
}

function redirectToLogin(request: NextRequest): NextResponse {
  return NextResponse.redirect(new URL(ROUTES.login, request.url));
}

function clearSessionCookies(response: NextResponse): void {
  response.cookies.delete(AUTH_COOKIES.access);
  response.cookies.delete(AUTH_COOKIES.refresh);
}

/**
 * Only these paths run the proxy. The matcher is literal because Next reads it
 * statically at build time. Add a path here when you add a protected route.
 */
export const config = {
  matcher: ["/dashboard", "/dashboard/:path*"],
};
