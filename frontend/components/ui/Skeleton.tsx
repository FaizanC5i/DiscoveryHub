import { cn } from "@/lib/cn";

interface SkeletonProps {
  className?: string;
}

/** Placeholder block shown while content loads. */
export function Skeleton({ className }: SkeletonProps) {
  return <div aria-hidden="true" className={cn("animate-pulse rounded-chip bg-surface-disabled", className)} />;
}
