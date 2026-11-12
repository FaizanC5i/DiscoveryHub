"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";
import { Button } from "@/components/ui/Button";
import type { Source } from "../types/source";
import { deleteSource, reprocessSource } from "../services/contextService";
import { formatFileSize } from "../utils/fileValidation";
import { SourceStatusBadge } from "./SourceStatusBadge";

interface SourceItemProps {
  projectId: number;
  source: Source;
}

export function SourceItem({ projectId, source }: SourceItemProps) {
  const router = useRouter();
  const [busy, setBusy] = useState<"retry" | "remove" | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function run(action: "retry" | "remove") {
    setBusy(action);
    setError(null);
    try {
      if (action === "retry") {
        await reprocessSource(projectId, source.id);
      } else {
        await deleteSource(projectId, source.id);
      }
      router.refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Something went wrong. Please try again.");
    } finally {
      setBusy(null);
    }
  }

  return (
    <li className="flex flex-col gap-2 py-4">
      <div className="flex items-start justify-between gap-3">
        <div className="flex min-w-0 flex-col gap-1">
          <p className="truncate text-body-medium font-semibold text-fg" title={source.original_filename}>
            {source.title}
          </p>
          <p className="text-caption text-fg-muted">{formatFileSize(source.file_size_bytes)}</p>
        </div>
        <SourceStatusBadge status={source.processing_status} />
      </div>

      {source.failure_reason ? <p className="text-caption text-error">{source.failure_reason}</p> : null}
      {error ? (
        <p role="alert" className="text-caption text-error">
          {error}
        </p>
      ) : null}

      <div className="flex gap-2">
        {source.processing_status === "failed" ? (
          <Button
            size="sm"
            variant="outline"
            loading={busy === "retry"}
            disabled={busy !== null}
            onClick={() => run("retry")}
          >
            Retry
          </Button>
        ) : null}
        <Button
          size="sm"
          variant="outline"
          loading={busy === "remove"}
          disabled={busy !== null}
          onClick={() => run("remove")}
        >
          Remove
        </Button>
      </div>
    </li>
  );
}