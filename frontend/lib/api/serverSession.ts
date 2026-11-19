import "server-only";

import { cookies } from "next/headers";
import { redirect } from "next/navigation";
import { isApiError } from "@/lib/api/client";
import { ROUTES } from "@/lib/constants";

/** Builds the headers that forward the visitor's cookies to the backend. */
export async function sessionHeaders(): Promise<HeadersInit> {
  const cookieStore = await cookies();
  return { Cookie: cookieStore.toString() };
}

/** Sends the visitor to sign in when the session is missing or expired. */
export function handleSessionError(error: unknown): never {
  if (isApiError(error, "UNAUTHENTICATED") || isApiError(error, "SESSION_EXPIRED")) {
    redirect(ROUTES.login);
  }
  throw error;
}