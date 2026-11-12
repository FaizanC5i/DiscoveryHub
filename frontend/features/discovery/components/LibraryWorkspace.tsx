"use client";

import { useState, type ComponentProps, type ReactNode } from "react";
import { buttonClass } from "../utils/class-names";
import { ContextLibrary } from "./ContextLibrary";
import { PanelIcon } from "./icons";

type LibraryWorkspaceProps = Omit<ComponentProps<typeof ContextLibrary>, "onClose"> & {
  children: ReactNode;
};

/**
 * Two-column workspace: the page content on the left and the context library on the
 * right. The library can be hidden, and the toggle sits above the content.
 */
export function LibraryWorkspace({ children, ...library }: LibraryWorkspaceProps) {
  const [isLibraryOpen, setIsLibraryOpen] = useState(true);

  return (
    <div className="flex flex-col gap-(--space-4)">
      <div className="flex justify-end">
        <button
          type="button"
          onClick={() => setIsLibraryOpen((open) => !open)}
          aria-expanded={isLibraryOpen}
          aria-controls="context-library"
          className={buttonClass.subtle}
        >
          <PanelIcon />
          {isLibraryOpen ? "Hide context library" : "Show context library"}
        </button>
      </div>

      {/* Library panel is 320px wide (--space-64 + --space-16) */}
      <div
        className={`grid grid-cols-1 gap-(--space-5) ${
          isLibraryOpen ? "lg:grid-cols-[minmax(0,1fr)_calc(var(--space-64)+var(--space-16))]" : ""
        }`}
      >
        <div className="flex min-w-0 flex-col gap-(--space-6)">{children}</div>

        {isLibraryOpen && <ContextLibrary {...library} onClose={() => setIsLibraryOpen(false)} />}
      </div>
    </div>
  );
}
