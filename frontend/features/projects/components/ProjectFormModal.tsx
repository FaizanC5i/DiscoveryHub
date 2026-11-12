"use client";

import { Modal } from "@/components/ui/Modal";
import type { Project, ProjectInput } from "@/types/project";
import { createProject, updateProject } from "../services/projectService";
import type { ProjectFormValues } from "../types/projectForm";
import { toFormValues } from "../utils/projectInput";
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
  /** When set, the modal edits this project. When omitted, it creates a new one. */
  project?: Project;
  /** Called with the saved project after the API accepts it. */
  onSaved: (project: Project) => void;
}

/**
 * The create-project and edit-project dialog. One component handles both, so the
 * fields and validation can never drift apart between the two.
 */
export function ProjectFormModal({ open, onClose, project, onSaved }: ProjectFormModalProps) {
  const isEditing = project !== undefined;

  async function handleSubmit(input: ProjectInput) {
    const saved = project ? await updateProject(project.id, input) : await createProject(input);
    onSaved(saved);
  }

  return (
    <Modal open={open} onClose={onClose} title={isEditing ? "Edit project" : "Create a new project"}>
      <ProjectForm
        initialValues={project ? toFormValues(project) : EMPTY_FORM_VALUES}
        submitLabel={isEditing ? "Save changes" : "Continue"}
        onSubmit={handleSubmit}
        onCancel={onClose}
      />
    </Modal>
  );
}
