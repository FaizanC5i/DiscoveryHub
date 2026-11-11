const dateFormatter = new Intl.DateTimeFormat("en-GB", {
  day: "numeric",
  month: "short",
  year: "numeric",
});

/** Formats an ISO date, or returns null when the date is not set. */
export function formatProjectDate(value: string | null): string | null {
  return value ? dateFormatter.format(new Date(value)) : null;
}