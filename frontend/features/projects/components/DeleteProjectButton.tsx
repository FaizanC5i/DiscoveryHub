"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";
import { TrashIcon } from "@/components/icons";
import { Alert } from "@/components/ui/Alert";
import { Button } from "@/components/ui/Button";
import { Modal } from "@/components/ui/Modal";
import { ROUTES } from "@/lib/constants";
import type { Project } from "@/types/project";
import { deleteProject } from "../services/projectService";

interface DeleteProjectButtonProps {
  project: Project;
}

/**
 * Asks for confirmation, then deletes the project and everything under it.
 * Deleting cannot be undone, so the dialog says what will be removed.
 */
export function DeleteProjectButton({ project }: DeleteProjectButtonProps) {
  const router = useRouter();
  const [isOpen, setIsOpen] = useState(false);
  const [isDeleting, setIsDeleting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  function close() {
    if (isDeleting) return;
    setError(null);
    setIsOpen(false);
  }

  async function handleDelete() {
    setIsDeleting(true);
    setError(null);
    try {
      await deleteProject(project.id);
      // Close before leaving: the page can stay mounted, and the dialog must not reopen later.
      setIsOpen(false);
      router.push(ROUTES.dashboard);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "The project could not be deleted. Please try again.");
    } finally {
      setIsDeleting(false);
    }
  }

  return (
    <>
      <Button variant="outline" size="sm" onClick={() => setIsOpen(true)}>
        <TrashIcon className="size-4" />
        Delete
      </Button>
      <Modal open={isOpen} onClose={close} title="Delete this project?" dismissible={!isDeleting}>
        <div className="flex flex-col gap-6">
          <p className="m-0 text-body-large text-fg-muted">
            <span className="font-semibold text-fg">{project.name}</span> and all of its documents, extracted
            text and chunks will be permanently deleted. This cannot be undone.
          </p>
          {error && <Alert>{error}</Alert>}
          <div className="flex justify-end gap-3">
            <Button variant="outline" onClick={close} disabled={isDeleting}>
              Cancel
            </Button>
            <Button onClick={handleDelete} disabled={isDeleting}>
              {isDeleting ? "Deleting…" : "Delete project"}
            </Button>
          </div>
        </div>
      </Modal>
    </>
  );
}
