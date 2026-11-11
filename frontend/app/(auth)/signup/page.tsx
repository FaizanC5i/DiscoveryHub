import { Suspense } from "react";
import type { Metadata } from "next";
import { SignUpForm } from "@/features/auth/components/SignUpForm";

export const metadata: Metadata = {
  title: "Create account",
};

type SearchParams = Promise<{ email?: string | string[] }>;

/**
 * The login page links here with ?email=... after an unknown email is entered.
 *
 * Reading searchParams is a request-time read, so it must sit behind Suspense
 * (Cache Components requires this). The page passes the promise down without
 * awaiting it. Only the child awaits it, so the static shell with the empty form
 * can render straight away.
 */
export default function SignUpPage({ searchParams }: { searchParams: SearchParams }) {
  return (
    <Suspense fallback={<SignUpForm />}>
      <SignUpPageContent searchParams={searchParams} />
    </Suspense>
  );
}

async function SignUpPageContent({ searchParams }: { searchParams: SearchParams }) {
  const { email } = await searchParams;
  const initialEmail = typeof email === "string" ? email : "";
  return <SignUpForm initialEmail={initialEmail} />;
}
