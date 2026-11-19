import Link from "next/link";
import { ArrowRightIcon, DownloadIcon, NotesIcon } from "@/components/icons";
import { cardStyles } from "@/components/ui/Card";
import { cn } from "@/lib/cn";
import type { QuickAccessItem, QuickAccessKey } from "../types/dashboard";

const ICONS: Record<QuickAccessKey, typeof DownloadIcon> = {
  exports: DownloadIcon,
  "mom-assistant": NotesIcon,
};

interface QuickAccessCardProps {
  item: QuickAccessItem;
}

export function QuickAccessCard({ item }: QuickAccessCardProps) {
  const Icon = ICONS[item.key];

  return (
    <Link
      href={item.href}
      className={cn(
        cardStyles,
        "group flex items-center gap-4 p-5 transition-colors hover:border-border-brand",
      )}
    >
      <span className="flex size-10 shrink-0 items-center justify-center rounded-chip bg-surface-brand-subtle text-fg-brand">
        <Icon className="size-5" />
      </span>
      <span className="flex min-w-0 flex-1 flex-col gap-1">
        <span className="text-body-large font-semibold text-fg">{item.title}</span>
        <span className="text-body-small text-fg-muted">{item.description}</span>
      </span>
      <ArrowRightIcon className="size-4 shrink-0 text-icon transition-transform group-hover:translate-x-0.5" />
    </Link>
  );
}
