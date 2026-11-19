const updatedFormatter = new Intl.DateTimeFormat("en-US", {
  month: "short",
  day: "numeric",
  hour: "numeric",
  minute: "2-digit",
});

/** Formats a project's last-updated timestamp, for example "Nov 5, 5:49 PM". */
export function formatUpdatedAt(isoTimestamp: string): string {
  return updatedFormatter.format(new Date(isoTimestamp));
}
