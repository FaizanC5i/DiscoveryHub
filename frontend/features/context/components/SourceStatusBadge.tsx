import type { ComponentProps } from "react";
import { Badge } from "@/components/ui/Badge";
import type { SourceStatus, UploadState } from "../types/source";

type BadgeTone = ComponentProps<typeof Badge>["tone"];

const SOURCE_STATUS: Record<SourceStatus, { label: string; tone: BadgeTone }> = {
  processing: { label: "Processing", tone: "brand" },
  ready: { label: "Uploaded", tone: "success" },
  failed: { label: "Failed", tone: "error" },
};

const UPLOAD_STATE: Record<UploadState, { label: string; tone: BadgeTone }> = {
  queued: { label: "Queued", tone: "neutral" },
  uploading: { label: "Processing", tone: "brand" },
  done: { label: "Uploaded", tone: "success" },
  failed: { label: "Failed", tone: "error" },
};

export function SourceStatusBadge({ status }: { status: SourceStatus }) {
  const { label, tone } = SOURCE_STATUS[status];
  return <Badge tone={tone}>{label}</Badge>;
}

export function UploadStateBadge({ state }: { state: UploadState }) {
  const { label, tone } = UPLOAD_STATE[state];
  return <Badge tone={tone}>{label}</Badge>;
}