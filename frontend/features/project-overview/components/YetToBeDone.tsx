import { cn } from "@/lib/cn";

/** Placeholder for a content area that has no data yet. */
export function YetToBeDone({ className }: { className?: string }) {
  return (
    <div
      className={cn(
        "flex items-center justify-center rounded-card border border-dashed border-border-subtle bg-page px-4 py-6",
        className,
      )}
    >
      <p className="text-body-medium text-fg-muted">Yet to be done</p>
    </div>
  );
}

/** Disabled stand-in for a link or button whose feature is not built yet. */
export function ComingSoonAction({ label }: { label: string }) {
  return (
    <span
      aria-disabled="true"
      title="Yet to be done"
      className="text-body-medium font-semibold text-fg-disabled"
    >
      {label}
    </span>
  );
}