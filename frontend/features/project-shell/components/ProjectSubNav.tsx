"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { ChevronLeftIcon, PanelRightIcon } from "@/components/icons";
import { Button, buttonStyles } from "@/components/ui/Button";
import { useContextLibrary } from "@/features/context-library/hooks/useContextLibrary";
import { cn } from "@/lib/cn";
import { PROJECT_TABS } from "../constants";

export function ProjectSubNav({ projectId }: { projectId: string }) {
  const pathname = usePathname();
  const { isOpen, toggle } = useContextLibrary();

  return (
    <div className="border-b border-border-subtle bg-surface">
      <div className="grid h-14 grid-cols-[1fr_auto_1fr] items-center gap-4 px-4 sm:px-6 lg:px-8">
        <div className="flex">
          <Link href="/dashboard" className={buttonStyles({ variant: "outline", size: "sm" })}>
            <ChevronLeftIcon className="size-4" />
            Home
          </Link>
        </div>

        <nav aria-label="Project sections" className="flex h-full">
          {PROJECT_TABS.map(({ label, segment }) => {
            const href = `/projects/${projectId}/${segment}`;
            const isActive = pathname === href || pathname.startsWith(`${href}/`);

            return (
              <Link
                key={segment}
                href={href}
                aria-current={isActive ? "page" : undefined}
                className={cn(
                  "inline-flex h-full items-center border-b-2 px-4 text-body-medium font-semibold transition-colors",
                  "focus-visible:outline-2 focus-visible:-outline-offset-2 focus-visible:outline-border-brand-strong",
                  isActive
                    ? "border-accent text-accent"
                    : "border-transparent text-fg-secondary hover:bg-surface-muted",
                )}
              >
                {label}
              </Link>
            );
          })}
        </nav>

        <div className="hidden justify-end lg:flex">
          <Button variant="outline" size="sm" onClick={toggle} aria-expanded={isOpen}>
            <PanelRightIcon className="size-4" />
            {isOpen ? "Hide context library" : "Show context library"}
          </Button>
        </div>
      </div>
    </div>
  );
}