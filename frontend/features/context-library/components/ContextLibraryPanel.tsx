"use client";

import { CloseIcon, PlusIcon } from "@/components/icons";
import { Button } from "@/components/ui/Button";
import { useContextLibrary } from "../hooks/useContextLibrary";
import type { ContextLibrary } from "../types/contextLibrary";
import { DiscoveryProgressCard } from "./DiscoveryProgressCard";
import { SourceBrowser } from "./SourceBrowser";

/** Right-hand panel shared by every project tab. Visible from the lg breakpoint up. */
export function ContextLibraryPanel({ progress, sources }: ContextLibrary) {
  const { isOpen, close } = useContextLibrary();

  if (!isOpen) {
    return null;
  }

  return (
    <aside
      aria-label="Context library"
      className="hidden w-80 shrink-0 flex-col gap-4 border-l border-border-subtle bg-surface p-6 lg:flex"
    >
      <div className="flex items-center justify-between">
        <h2 className="text-title-small font-semibold text-fg">Context library</h2>
        <button
          type="button"
          onClick={close}
          aria-label="Close context library"
          className="rounded-control p-1 text-icon hover:text-icon-strong focus-visible:outline-2 focus-visible:outline-border-brand-strong"
        >
          <CloseIcon className="size-4" />
        </button>
      </div>

      <DiscoveryProgressCard progress={progress} />

      <div className="grid grid-cols-2 gap-2">
        <Button size="sm">
          <PlusIcon className="size-4" />
          Add Files
        </Button>
        <Button variant="outline" size="sm">
          <PlusIcon className="size-4" />
          Add Note
        </Button>
      </div>
      <p className="text-caption text-fg-muted">
        Drop files anywhere in this project, or use Add files, or add a Note
      </p>

      <SourceBrowser sources={sources} />
    </aside>
  );
}