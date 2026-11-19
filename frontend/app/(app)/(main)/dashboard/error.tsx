"use client";

import { ErrorState } from "@/components/feedback/ErrorState";

export default function DashboardError({ reset }: { error: Error; reset: () => void }) {
  return (
    <ErrorState
      title="We couldn't load your dashboard"
      message="Something went wrong while loading your projects. Please try again."
      onRetry={reset}
    />
  );
}
