import type { Metadata } from "next";
import { Suspense } from "react";
import { AuthLanding } from "@/features/auth/components/landing/AuthLanding";

export const metadata: Metadata = {
  title: "Create account",
};

type SearchParams = Promise<{ email?: string | string[] }>;

/**
 * /signup opens the sign-up panel. The sign-in panel links here with ?email=... after an unknown
 * email. Reading searchParams must sit behind Suspense (Cache Components requires this).
 */
export default function SignUpPage({ searchParams }: { searchParams: SearchParams }) {
  return (
    <Suspense fallback={<AuthLanding initialMode="signup" />}>
      <SignUpPageContent searchParams={searchParams} />
    </Suspense>
  );
}

async function SignUpPageContent({ searchParams }: { searchParams: SearchParams }) {
  const { email } = await searchParams;
  return <AuthLanding initialMode="signup" initialEmail={typeof email === "string" ? email : ""} />;
}
