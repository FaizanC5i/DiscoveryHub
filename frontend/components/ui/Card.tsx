import type { HTMLAttributes } from "react";
import { cn } from "@/lib/cn";

/** Shared surface styling for cards, used by Card and by link-based cards. */
export const cardStyles = "rounded-card border border-border-subtle bg-surface";

export function Card({ className, ...props }: HTMLAttributes<HTMLDivElement>) {
  return <div className={cn(cardStyles, className)} {...props} />;
}
