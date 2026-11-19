import type { SelectHTMLAttributes } from "react";
import { ChevronDownIcon } from "@/components/icons";
import { cn } from "@/lib/cn";

/** Native select styled with the Dropdown/* component tokens. */
export function Select({ className, children, ...props }: SelectHTMLAttributes<HTMLSelectElement>) {
  return (
    <div className="relative">
      <select
        className={cn(
          "h-11 w-full appearance-none rounded-control border border-border bg-surface pr-9 pl-3 text-body-medium text-fg outline-none transition-colors",
          "hover:border-border-brand focus:border-border-brand-strong",
          "disabled:border-border-disabled disabled:bg-surface-disabled disabled:text-fg-disabled",
          className,
        )}
        {...props}
      >
        {children}
      </select>
      <ChevronDownIcon className="pointer-events-none absolute top-1/2 right-3 size-4 -translate-y-1/2 text-icon" />
    </div>
  );
}