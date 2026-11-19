const dateFormatter = new Intl.DateTimeFormat("en-GB", {
  day: "numeric",
  month: "short",
  year: "numeric",
});

const timestampFormatter = new Intl.DateTimeFormat("en-GB", {
  day: "numeric",
  month: "short",
  year: "numeric",
  hour: "2-digit",
  minute: "2-digit",
});

/** Formats a "YYYY-MM-DD" date, or returns null when the date is not set. */
export function formatProjectDate(value: string | null): string | null {
  if (!value) return null;
  // Parse the date parts directly. new Date("2026-11-01") is read as UTC and can show the day before in some time zones.
  const [year, month, day] = value.split("-").map(Number);
  return dateFormatter.format(new Date(year, month - 1, day));
}

/** Formats an ISO timestamp with a UTC offset, in the viewer's local time. */
export function formatProjectTimestamp(isoTimestamp: string): string {
  return timestampFormatter.format(new Date(isoTimestamp));
}
