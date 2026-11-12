"use client";

import { ErrorState } from "@/components/feedback/ErrorState";

export default function ProjectOverviewError({ reset }: { error: Error; reset: () => void }) {
  return (
    <ErrorState
      title="We couldn't load this project"
      message="Something went wrong while loading the project. Please try again."
      onRetry={reset}
    />
  );
}
