import type { DraftSection } from "../types/artifact-studio.types";
import { SECTION_STATUS, sectionNumber } from "../utils/section-status";

interface DraftSectionNavProps {
  sections: DraftSection[];
  activeId: string;
  onSelect: (id: string) => void;
}

/** Left column: list of sections with their status. */
export function DraftSectionNav({ sections, activeId, onSelect }: DraftSectionNavProps) {
  return (
    <nav aria-label="Document sections" className="border-b lg:border-b-0 lg:border-r border-(--color-border-default-disabled) bg-(--color-bg-default-primary) p-(--space-3)">
      <ul className="m-0 flex list-none flex-col gap-(--space-1) p-0">
        {sections.map((section) => {
          const isActive = section.id === activeId;
          const status = SECTION_STATUS[section.status];
          return (
            <li key={section.id}>
              <button
                type="button"
                onClick={() => onSelect(section.id)}
                aria-current={isActive ? "true" : undefined}
                className={`flex w-full cursor-pointer flex-col items-start gap-(--space-1) rounded-(--radius-md) border-0 border-l-(length:--space-1) px-(--space-3) py-(--space-3) text-left ${
                  isActive
                    ? "border-(--color-border-brand-primary) bg-(--color-bg-brand-subtle)"
                    : "border-transparent bg-transparent hover:bg-(--color-bg-default-secondary)"
                }`}
              >
                <span
                  className={`text-(length:--font-size-body-small) leading-(--line-height-body-small) font-semibold ${
                    isActive ? "text-(--color-text-brand-primary)" : "text-(--color-text-default-primary)"
                  }`}
                >
                  {sectionNumber(section.number)} {section.title}
                </span>
                <span className={status.badge}>{status.label}</span>
              </button>
            </li>
          );
        })}
      </ul>
    </nav>
  );
}