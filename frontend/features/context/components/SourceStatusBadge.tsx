import type { ComponentProps } from "react";
import { Badge } from "@/components/ui/Badge";
import type { SourceStatus, SourceType, UploadState } from "../types/source";
import { ProcessingBadge } from "./ProcessingIndicator";

type BadgeTone = ComponentProps<typeof Badge>["tone"];

const SOURCE_STATUS: Record<SourceStatus, { label: string; tone: BadgeTone }> = {
  processing: { label: "Processing", tone: "brand" },
  ready: { label: "Uploaded", tone: "success" },
  failed: { label: "Failed", tone: "error" },
};

const NOTE_STATUS: Record<SourceStatus, { label: string; tone: BadgeTone }> = {
  ...SOURCE_STATUS,
  ready: { label: "Processed", tone: "success" },
};

const UPLOAD_STATE: Record<UploadState, { label: string; tone: BadgeTone }> = {
  queued: { label: "Queued", tone: "neutral" },
  uploading: { label: "Processing", tone: "brand" },
  done: { label: "Uploaded", tone: "success" },
  failed: { label: "Failed", tone: "error" },
};

interface SourceStatusBadgeProps {
  status: SourceStatus;
  sourceType?: SourceType;
  /** The helper agent is still mapping this source's chunks. Shown as processing until it finishes. */
  mappingPending?: boolean;
}

export function SourceStatusBadge({ status, sourceType = "FILE_UPLOAD", mappingPending = false }: SourceStatusBadgeProps) {
  if (status === "processing" || mappingPending) return <ProcessingBadge />;
  const { label, tone } = (sourceType === "MANUAL_NOTE" ? NOTE_STATUS : SOURCE_STATUS)[status];
  return <Badge tone={tone}>{label}</Badge>;
}

export function UploadStateBadge({ state }: { state: UploadState }) {
  const { label, tone } = UPLOAD_STATE[state];
  return <Badge tone={tone}>{label}</Badge>;
}
