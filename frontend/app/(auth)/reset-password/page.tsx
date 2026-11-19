import { Suspense } from "react";
import type { Metadata } from "next";
import { FullPageLoader } from "@/components/feedback/FullPageLoader";
import { ResetPasswordForm } from "@/features/auth/components/ResetPasswordForm";

export const metadata: Metadata = {
  title: "Reset password",
};

type SearchParams = Promise<{ token?: string | string[] }>;

/**
 * The emailed link looks like /reset-password?token=... The token is read on the
 * server and passed to the form, which sends it to the backend exactly once.
 *
 * searchParams is a request-time read, so it sits behind Suspense. The page passes
 * the promise down without awaiting it, and only the child awaits it.
 */
export default function ResetPasswordPage({ searchParams }: { searchParams: SearchParams }) {
  return (
    <Suspense fallback={<FullPageLoader label="Loading reset link" />}>
      <ResetPasswordPageContent searchParams={searchParams} />
    </Suspense>
  );
}

async function ResetPasswordPageContent({ searchParams }: { searchParams: SearchParams }) {
  const { token } = await searchParams;
  return <ResetPasswordForm token={typeof token === "string" ? token : ""} />;
}
