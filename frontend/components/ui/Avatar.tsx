import { cn } from "@/lib/cn";

interface AvatarProps {
  name: string;
  className?: string;
}

/** Initials avatar. Initials come from the first and last word of the name. */
export function Avatar({ name, className }: AvatarProps) {
  const initials = getInitials(name);

  return (
    <span
      aria-hidden="true"
      className={cn(
        "flex size-8 shrink-0 items-center justify-center rounded-full bg-surface-brand-subtle text-caption font-semibold text-fg-brand",
        className,
      )}
    >
      {initials}
    </span>
  );
}

function getInitials(name: string): string {
  const words = name.trim().split(/\s+/).filter(Boolean);
  if (words.length === 0) {
    return "";
  }
  const first = words[0][0];
  const last = words.length > 1 ? words[words.length - 1][0] : "";
  return `${first}${last}`.toUpperCase();
}
