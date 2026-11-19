import { FileDropzone } from "@/features/context/components/FileDropzone";
import { PendingFileList } from "@/features/context/components/PendingFileList";
import type { PendingFile } from "@/features/context/types/source";

interface ProjectDocumentsFieldProps {
  files: PendingFile[];
  fileError: string | null;
  onFilesSelected: (files: File[]) => void;
  onRemove: (id: string) => void;
}

export function ProjectDocumentsField({
  files,
  fileError,
  onFilesSelected,
  onRemove,
}: ProjectDocumentsFieldProps) {
  return (
    <section className="flex flex-col gap-3">
      <div className="flex flex-col gap-1">
        <h3 className="text-title-small font-semibold text-fg">Project documents</h3>
        <p className="text-body-small text-fg-muted">
          Meeting notes, requirements, process documents. They are processed when you click Continue.
        </p>
      </div>

      <FileDropzone onFilesSelected={onFilesSelected} />

      {fileError ? (
        <p role="alert" className="text-body-small text-error">
          {fileError}
        </p>
      ) : null}

      <PendingFileList files={files} onRemove={onRemove} />
    </section>
  );
}