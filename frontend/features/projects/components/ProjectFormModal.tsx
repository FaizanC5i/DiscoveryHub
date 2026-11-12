"use client";

import { useEffect, useState } from "react";
import { Modal } from "@/components/ui/Modal";
import { useSourceUploads } from "@/features/context/hooks/useSourceUploads";
import type { Project, ProjectInput } from "@/types/project";
import { createProject, updateProject } from "../services/projectService";
import type { ProjectFormValues } from "../types/projectForm";
import { toFormValues } from "../utils/projectInput";
import { ProjectDocumentsField } from "./ProjectDocumentsField";
import { ProjectDocumentsStep } from "./ProjectDocumentsStep";
import { ProjectForm } from "./ProjectForm";

const EMPTY_FORM_VALUES: ProjectFormValues = {
  name: "",
  description: "",
  startDate: "",
  endDate: "",
};

interface ProjectFormModalProps {
  open: boolean;
  onClose: () => void;
  /** When set, the modal edits this project. When omitted, it creates one. */
  project?: Project;
  /** Called once the project is saved and every document is ready. */
  onSaved: (project: Project) => void;
}

/**
 * Create and edit dialog. Create mode has two steps:
 *   1. The form. Continue creates the project and sends the documents.
 *   2. The documents step. Shown while uploads run, and kept open with Retry if any fail.
 *
 * The dialog closes itself only when everything is ready. While uploads run it
 * cannot be dismissed, so a file is never abandoned half-sent.
 */
export function ProjectFormModal({ open, onClose, project, onSaved }: ProjectFormModalProps) {
  const isEditing = project !== undefined;
  const [created, setCreated] = useState<Project | null>(null);
  const { files, fileError, isUploading, addFiles, removeFile, uploadFiles, reset } =
    useSourceUploads();

  useEffect(() => {
    if (!open) {
      setCreated(null);
      reset();
    }
  }, [open, reset]);

  async function handleSubmit(input: ProjectInput) {
    if (project) {
      onSaved(await updateProject(project.id, input));
      return;
    }

    const newProject = await createProject(input);
    setCreated(newProject);

    const allReady = await uploadFiles(newProject.id, files);
    if (allReady) onSaved(newProject);
  }

  async function handleRetry() {
    if (!created) return;
    const failed = files.filter((file) => file.state === "failed");
    const allReady = await uploadFiles(created.id, failed);
    if (allReady) onSaved(created);
  }

  const title = isEditing ? "Edit project" : created ? "Project documents" : "Create a new project";

  return (
    <Modal open={open} onClose={onClose} title={title} dismissible={!isUploading}>
      {created !== null ? (
        <ProjectDocumentsStep
          projectName={created.name}
          files={files}
          isUploading={isUploading}
          onRetry={handleRetry}
          onOpenProject={() => onSaved(created)}
        />
      ) : (
        <ProjectForm
          initialValues={project ? toFormValues(project) : EMPTY_FORM_VALUES}
          submitLabel={isEditing ? "Save changes" : "Continue"}
          onSubmit={handleSubmit}
          onCancel={onClose}
          documents={
            isEditing ? undefined : (
              <ProjectDocumentsField
                files={files}
                fileError={fileError}
                onFilesSelected={addFiles}
                onRemove={removeFile}
              />
            )
          }
        />
      )}
    </Modal>
  );
}