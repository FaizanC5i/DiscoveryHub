import Link from "next/link";
import { buttonClass } from "../utils/class-names";
import { SettingsIcon } from "./icons";

interface DiscoveryHeaderProps {
  projectName: string;
  userName: string;
}

/** "AK" from "Alex Kim". */
function getInitials(name: string): string {
  return name
    .split(" ")
    .filter(Boolean)
    .slice(0, 2)
    .map((part) => part[0]!.toUpperCase())
    .join("");
}

/** Top bar: logo, project name in the centre, user and Settings on the right. */
export function DiscoveryHeader({ projectName, userName }: DiscoveryHeaderProps) {
  return (
    <header className="grid grid-cols-[1fr_auto] md:grid-cols-[1fr_auto_1fr] items-center gap-(--space-4) border-b border-(--color-border-default-disabled) bg-(--color-bg-default-primary) px-(--space-4) md:px-(--space-7) py-(--space-3)">
      {/* PLACEHOLDER logo: swap for the C5i logo used on the dashboard. */}
      <Link href="/dashboard" className="inline-flex items-center gap-(--space-3) text-(--color-text-default-primary) no-underline">
        <span
          aria-hidden="true"
          className="inline-grid size-(--space-7) place-items-center rounded-(--radius-md) bg-(--color-bg-brand-primary) text-(length:--font-size-body-large) leading-(--line-height-body-large) font-bold text-(--color-text-default-inverse)"
        >
          D
        </span>
        <span className="text-(length:--font-size-title-small) leading-(--line-height-title-small) font-semibold">
          Discovery Hub
        </span>
      </Link>

      <h1 className="m-0 hidden md:block text-center text-(length:--font-size-title-small) leading-(--line-height-title-small) font-semibold">
        {projectName}
      </h1>

      <div className="flex items-center justify-end gap-(--space-3)">
        <span
          aria-hidden="true"
          className="inline-grid size-(--space-10) place-items-center rounded-full bg-(--color-bg-brand-subtle) text-(length:--font-size-body-small) leading-(--line-height-body-small) font-semibold text-(--color-text-brand-primary)"
        >
          {getInitials(userName)}
        </span>
        <span className="hidden md:inline text-(length:--font-size-body-medium) leading-(--line-height-body-medium) font-medium">
          {userName}
        </span>
        <Link href="/settings" className={buttonClass.subtle}>
          <SettingsIcon />
          Settings
        </Link>
      </div>
    </header>
  );
}