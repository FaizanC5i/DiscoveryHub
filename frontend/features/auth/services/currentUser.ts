import "server-only";

import { cache } from "react";
import { cookies } from "next/headers";
import { redirect } from "next/navigation";
import { apiRequest, isApiError } from "@/lib/api/client";
import { API_PATHS } from "@/lib/api/endpoints";
import { ROUTES } from "@/lib/constants";
import type { User } from "@/types/user";
import { MOCK_USER, USE_MOCK_AUTH } from "./authService";

/**
 * Server-only: returns the signed-in user, or sends the visitor to the login page.
 *
 * Analogy: the bouncer at the door of the members' area. Every page inside calls
 * this check, and nobody gets past without a valid wristband (the access cookie)
 * that the backend accepts.
 *
 * Why the server and not the browser? A browser can hide a page, but it cannot
 * stop the server from sending the page's data. Checking here means the
 * dashboard's data is never rendered or sent to someone who is not signed in.
 *
 * `import "server-only"` makes the build fail if a client component imports this
 * file by mistake, which would expose server-side session handling to the browser.
 *
 * Wrapped in React's cache(): the layout and the dashboard page both call this
 * during one request, and cache() makes them share a single backend call.
 */
export const getCurrentUser = cache(async (): Promise<User> => {
  if (USE_MOCK_AUTH) {
    return MOCK_USER;
  }

  // Forward the visitor's cookies to the backend. Server code has no browser
  // cookie jar of its own, so it must pass the cookie header on by hand.
  const cookieStore = await cookies();

  try {
    return await apiRequest<User>(API_PATHS.auth.me, {
      method: "GET",
      headers: { Cookie: cookieStore.toString() },
      cache: "no-store", // session state must never be served from a cache
      skipAuthRefresh: true, // a server component cannot set cookies, so refreshing here is impossible
    });
  } catch (error) {
    // redirect() works by throwing, so it must sit outside the try block above
    // (it is in the catch, which is fine). Any other error propagates unchanged.
    if (isApiError(error, "UNAUTHENTICATED") || isApiError(error, "SESSION_EXPIRED")) {
      redirect(ROUTES.login);
    }
    throw error;
  }
});
