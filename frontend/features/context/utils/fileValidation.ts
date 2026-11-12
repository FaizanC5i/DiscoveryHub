export const UPLOAD_MAX_BYTES = 20 * 1024 * 1024;

export const ACCEPTED_EXTENSIONS = [".pdf", ".docx", ".txt", ".md"] as const;

export const ACCEPT_ATTRIBUTE = ACCEPTED_EXTENSIONS.join(",");

/** Returns an error message, or null when the file can be uploaded. Mirrors the backend rules. */
export function validateUploadFile(file: File): string | null {
  const dot = file.name.lastIndexOf(".");
  const extension = dot >= 0 ? file.name.slice(dot).toLowerCase() : "";

  if (!ACCEPTED_EXTENSIONS.includes(extension as (typeof ACCEPTED_EXTENSIONS)[number])) {
    return `${file.name} is not a supported file type.`;
  }
  if (file.size === 0) {
    return `${file.name} is empty.`;
  }
  if (file.size > UPLOAD_MAX_BYTES) {
    return `${file.name} is larger than 20 MB.`;
  }
  return null;
}

export function formatFileSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${Math.round(bytes / 1024)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}