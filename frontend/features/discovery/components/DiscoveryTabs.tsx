import Link from "next/link";
import { buttonClass } from "../utils/class-names";
import { ChevronLeftIcon, PanelIcon } from "./icons";

export type WorkspaceTab = "workspace" | "discovery" | "studio";

interface DiscoveryTabsProps {
  projectId: string;
  activeTab: WorkspaceTab;
  isLibraryOpen: boolean;
  onToggleLibrary: () => void;
}

/** Second bar: "All projects", the three project tabs, and the library toggle. */
export function DiscoveryTabs({ projectId, activeTab, isLibraryOpen, onToggleLibrary }: DiscoveryTabsProps) {
  const tabs = [
    { label: "Workspace", href: `/projects/${projectId}`, active: activeTab === "workspace" },
    { label: "Discovery Hub", href: `/projects/${projectId}/discovery`, active: activeTab === "discovery" },
    { label: "Artifact Studio", href: `/projects/${projectId}/studio`, active: activeTab === "studio" },
  ];

  return (
    <nav
      aria-label="Project"
      className="grid grid-cols-[auto_1fr] md:grid-cols-[1fr_auto_1fr] items-center gap-(--space-4) border-b border-(--color-border-default-disabled) bg-(--color-bg-default-primary) px-(--space-4) md:px-(--space-7) py-(--space-3)"
    >
      <div>
        <Link href="/dashboard" className={buttonClass.subtle}>
          <ChevronLeftIcon />
          All projects
        </Link>
      </div>

      <ul className="order-3 md:order-none col-span-2 md:col-span-1 m-0 flex list-none gap-(--space-2) overflow-x-auto p-0">
        {tabs.map((tab) => (
          <li key={tab.label}>
            <Link
              href={tab.href}
              aria-current={tab.active ? "page" : undefined}
              className={`inline-block whitespace-nowrap rounded-(--radius-md) px-(--space-4) py-(--space-2) text-(length:--font-size-body-medium) leading-(--line-height-body-medium) font-medium no-underline ${
                tab.active
                  ? "bg-(--color-bg-brand-subtle) text-(--color-primary-default)"
                  : "text-(--color-text-default-secondary) hover:bg-(--color-bg-default-subtle)"
              }`}
            >
              {tab.label}
            </Link>
          </li>
        ))}
      </ul>

      <div className="flex justify-end">
        <button
          type="button"
          onClick={onToggleLibrary}
          aria-expanded={isLibraryOpen}
          aria-controls="context-library"
          className={buttonClass.subtle}
        >
          <PanelIcon />
          {isLibraryOpen ? "Hide context library" : "Show context library"}
        </button>
      </div>
    </nav>
  );
}