import { cn } from "@/lib/cn";

/** A small pulsing dot with a label, shown in place of a status while a source is being processed. */
export function ProcessingBadge({ label = "Processing" }: { label?: string }) {
  return (
    <span
      className="inline-flex shrink-0 items-center gap-2 rounded-chip bg-badge-brand-bg px-2 py-0.5 text-caption font-medium text-badge-brand-fg"
    >
      <span className="relative flex size-2">
        <span className="absolute inline-flex size-full animate-ping rounded-full bg-accent opacity-75 motion-reduce:animate-none" />
        <span className="relative inline-flex size-2 rounded-full bg-accent" />
      </span>
      {label}
    </span>
  );
}

/** A thin track with a light sweeping across it. It says work is running without saying how far along. */
export function ShimmerBar({ className }: { className?: string }) {
  return (
    <div aria-hidden="true" className={cn("relative h-1 w-full overflow-hidden rounded-full bg-surface-disabled", className)}>
      <div className="absolute inset-y-0 left-0 w-1/3 rounded-full bg-linear-to-r from-transparent via-accent to-transparent animate-context-shimmer motion-reduce:animate-none" />
    </div>
  );
}

/** Shown above the source list while at least one file or note is still being processed. */
export function ProcessingPanel({ count }: { count: number }) {
  return (
    <div role="status" className="flex flex-col gap-3 rounded-card bg-page p-4">
      <div className="flex items-center justify-between gap-3">
        <p className="text-body-small font-semibold text-fg">
          {count === 1 ? "Processing 1 item" : `Processing ${count} items`}
        </p>
        <ProcessingBadge label="In progress" />
      </div>
      <ShimmerBar />
      <p className="text-caption text-fg-muted">
        Extracting text, splitting it into sections and mapping it to discovery checkpoints.
      </p>
    </div>
  );
}
