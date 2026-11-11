import type { ReactNode } from "react";
import { Logo } from "@/components/brand/Logo";
import { ROUTES } from "@/lib/constants";
import { AuthBrandPanel } from "./AuthBrandPanel";

interface AuthShellProps {
  children: ReactNode;
}

/** Two-column auth layout. The brand panel moves out of the way below the lg breakpoint. */
export function AuthShell({ children }: AuthShellProps) {
  return (
    <div className="grid min-h-dvh grid-cols-1 lg:grid-cols-2">
      <div className="hidden bg-page p-4 lg:block">
        <AuthBrandPanel />
      </div>

      <main className="flex items-center justify-center bg-surface px-4 py-12 sm:px-6 lg:px-12">
        <div className="flex w-full max-w-md flex-col">
          <div className="mb-10 lg:hidden">
            <Logo href={ROUTES.login} />
          </div>
          {children}
        </div>
      </main>
    </div>
  );
}
