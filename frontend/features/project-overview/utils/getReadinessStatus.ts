/** Label for the readiness ring, derived from the percentage so it can never contradict it. */
export function getReadinessStatus(percentComplete: number): string {
  if (percentComplete <= 0) return "Not started";
  if (percentComplete >= 100) return "Complete";
  return "In progress";
}