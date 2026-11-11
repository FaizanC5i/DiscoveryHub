"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/Button";
import { ROUTES } from "@/lib/constants";
import { authService } from "../services/authService";

/**
 * Ends the session on the backend, then returns to the login page.
 *
 * Order matters: the server must revoke the session before we navigate. If the
 * request fails, we stay here and show the error, instead of pretending the user
 * is signed out while their session is still valid.
 */
export function LogoutButton() {
  const router = useRouter();
  const [isSigningOut, setIsSigningOut] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSignOut() {
    setIsSigningOut(true);
    setError(null);
    try {
      await authService.logout();
      router.replace(ROUTES.login);
      router.refresh();
    } catch {
      setError("Could not sign out. Please try again.");
      setIsSigningOut(false);
    }
  }

  return (
    <div className="flex items-center gap-2">
      {error ? (
        <p role="alert" className="text-caption text-error">
          {error}
        </p>
      ) : null}
      <Button variant="subtle" size="sm" onClick={handleSignOut} loading={isSigningOut}>
        Sign out
      </Button>
    </div>
  );
}
