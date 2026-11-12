"use client";

import { useCallback, useState } from "react";
import { reprocessSource, uploadSource } from "../services/contextService";
import type { PendingFile, UploadState } from "../types/source";
import { validateUploadFile } from "../utils/fileValidation";

/**
 * Upload state for a list of files: picking, validating, sending one at a time,
 * and retrying. The create-project modal and the overview panel both use it.
 */
export function useSourceUploads() {
  const [files, setFiles] = useState<PendingFile[]>([]);
  const [fileError, setFileError] = useState<string | null>(null);
  const [isUploading, setIsUploading] = useState(false);

  const updateFile = useCallback((id: string, changes: Partial<PendingFile>) => {
    setFiles((previous) => previous.map((file) => (file.id === id ? { ...file, ...changes } : file)));
  }, []);

  /** Validates the picked files and adds the valid ones. Returns the files that were added. */
  const addFiles = useCallback((selected: File[]): PendingFile[] => {
    const accepted: PendingFile[] = [];
    const errors: string[] = [];

    for (const file of selected) {
      const error = validateUploadFile(file);
      if (error) {
        errors.push(error);
      } else {
        accepted.push({ id: crypto.randomUUID(), file, state: "queued" });
      }
    }

    setFileError(errors.length > 0 ? errors.join(" ") : null);
    setFiles((previous) => [...previous, ...accepted]);
    return accepted;
  }, []);

  const removeFile = useCallback((id: string) => {
    setFiles((previous) => previous.filter((file) => file.id !== id));
  }, []);

  /** Forget everything. Used when the dialog closes. */
  const reset = useCallback(() => {
    setFiles([]);
    setFileError(null);
  }, []);

  /** Drop files the server has already saved, because they now appear in the library. */
  const dropSavedFiles = useCallback(() => {
    setFiles((previous) => previous.filter((file) => file.sourceId === undefined));
  }, []);

  const uploadOne = useCallback(
    async (projectId: number, item: PendingFile): Promise<boolean> => {
      updateFile(item.id, { state: "uploading", error: undefined });
      try {
        const source =
          item.sourceId !== undefined
            ? await reprocessSource(projectId, item.sourceId)
            : await uploadSource(projectId, item.file);

        const state: UploadState = source.processing_status === "ready" ? "done" : "failed";
        updateFile(item.id, {
          sourceId: source.id,
          state,
          error: source.failure_reason ?? undefined,
        });
        return state === "done";
      } catch (error) {
        updateFile(item.id, {
          state: "failed",
          error: error instanceof Error ? error.message : "Upload failed. Please try again.",
        });
        return false;
      }
    },
    [updateFile],
  );

  /** Sends the given files one after another. Resolves true only when every one is ready. */
  const uploadFiles = useCallback(
    async (projectId: number, items: PendingFile[]): Promise<boolean> => {
      setIsUploading(true);
      let allReady = true;
      try {
        for (const item of items) {
          const ok = await uploadOne(projectId, item);
          allReady = allReady && ok;
        }
      } finally {
        setIsUploading(false);
      }
      return allReady;
    },
    [uploadOne],
  );

  return {
    files,
    fileError,
    isUploading,
    addFiles,
    removeFile,
    uploadFiles,
    dropSavedFiles,
    reset,
  };
}