import type { ReactNode } from "react";
import { AppHeader } from "@/components/layout/AppHeader";
import { getCurrentUser } from "@/features/auth/services/currentUser";

/** Chrome for regular pages: header plus a centered, width-limited content area. */
export default async function MainLayout({ children }: { children: ReactNode }) {
  const user = await getCurrentUser();

  return (
    <div className="flex min-h-dvh flex-col">
      <AppHeader user={user} />
      <main className="mx-auto w-full max-w-5xl flex-1 px-4 py-10 sm:px-6 lg:px-8">{children}</main>
    </div>
  );
}