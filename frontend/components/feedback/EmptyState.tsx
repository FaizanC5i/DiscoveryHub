import type { ReactNode } from "react";
import { cardStyles } from "@/components/ui/Card";
import { cn } from "@/lib/cn";

interface EmptyStateProps {
  title: string;
  description: string;
  action?: ReactNode;
  className?: string;
}

/** Shown when a list has no items yet. */
export function EmptyState({ title, description, action, className }: EmptyStateProps) {
  return (
    <div
      className={cn(
        cardStyles,
        "flex flex-col items-start gap-2 border-dashed p-6 sm:flex-row sm:items-center sm:justify-between",
        className,
      )}
    >
      <div className="flex flex-col gap-1">
        <h3 className="text-body-large font-semibold text-fg">{title}</h3>
        <p className="text-body-medium text-fg-muted">{description}</p>
      </div>
      {action}
    </div>
  );
}
