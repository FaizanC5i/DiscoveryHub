"use client";

import { useState, type ReactNode } from "react";
import { Button } from "@/components/ui/Button";
import { cn } from "@/lib/cn";
import type { Source } from "../types/source";
import { ContextLibrary } from "./ContextLibrary";

interface ContextLibraryWorkspaceProps {
  projectId: number;
  sources: Source[];
  children: ReactNode;
}

/**
 * The page content on the left and the context library on the right. Every project
 * tab uses this, so the library looks and behaves the same everywhere.
 */
export function ContextLibraryWorkspace({ projectId, sources, children }: ContextLibraryWorkspaceProps) {
  const [isLibraryOpen, setIsLibraryOpen] = useState(true);

  return (
    <div className="flex flex-col gap-4">
      <div className="flex justify-end">
        <Button variant="outline" size="sm" onClick={() => setIsLibraryOpen((open) => !open)}>
          {isLibraryOpen ? "Hide context library" : "Show context library"}
        </Button>
      </div>

      <div
        className={cn(
          "grid gap-6",
          isLibraryOpen && "lg:grid-cols-[minmax(0,1fr)_340px] lg:items-start",
        )}
      >
        <div className="flex min-w-0 flex-col gap-6">{children}</div>

        {isLibraryOpen ? (
          <div className="lg:sticky lg:top-6">
            <ContextLibrary projectId={projectId} sources={sources} onHide={() => setIsLibraryOpen(false)} />
          </div>
        ) : null}
      </div>
    </div>
  );
}
