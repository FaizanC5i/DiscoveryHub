import { Suspense, type ReactNode } from "react";
import { AppHeader } from "@/components/layout/AppHeader";
import { FullPageLoader } from "@/components/feedback/FullPageLoader";
import { getCurrentUser } from "@/features/auth/services/currentUser";

/**
 * Layout for every signed-in page.
 *
 * The layout itself is synchronous. The session check lives in AuthenticatedShell,
 * inside a Suspense boundary. Reading cookies at the top level of a layout would
 * make the whole route wait on the request, and Cache Components rejects cookie
 * reads that are not under a Suspense boundary.
 *
 * Analogy: the lobby of a members' club. The sign is visible straight away, and
 * the member check happens at the door of the lounge. Anyone who fails the check
 * is turned away before any member content reaches the screen.
 */
export default function AppLayout({ children }: { children: ReactNode }) {
  return (
    <Suspense fallback={<FullPageLoader label="Checking your session" />}>
      <AuthenticatedShell>{children}</AuthenticatedShell>
    </Suspense>
  );
}

/**
 * Runs the session check, then renders the app chrome around the page.
 * getCurrentUser() redirects to /login when the visitor is not signed in, so
 * nothing below it renders for them. The proxy has usually already handled the
 * redirect; this is the backstop for a session that was revoked after the proxy ran.
 */
async function AuthenticatedShell({ children }: { children: ReactNode }) {
  const user = await getCurrentUser();

  return (
    <div className="flex min-h-dvh flex-col">
      <AppHeader user={user} />
      <main className="mx-auto w-full max-w-5xl flex-1 px-4 py-10 sm:px-6 lg:px-8">{children}</main>
    </div>
  );
}
