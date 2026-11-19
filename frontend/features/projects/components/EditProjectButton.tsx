"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";
import { PencilIcon } from "@/components/icons";
import { Button } from "@/components/ui/Button";
import type { Project } from "@/types/project";
import { ProjectFormModal } from "./ProjectFormModal";

interface EditProjectButtonProps {
  project: Project;
}

/**
 * Opens the same dialog as "create", pre-filled with the saved values. On save, the
 * overview is re-fetched so the page shows the new details.
 */
export function EditProjectButton({ project }: EditProjectButtonProps) {
  const router = useRouter();
  const [isOpen, setIsOpen] = useState(false);

  return (
    <>
      <Button variant="secondary" size="sm" onClick={() => setIsOpen(true)}>
        <PencilIcon className="size-4" />
        Edit
      </Button>
      <ProjectFormModal
        open={isOpen}
        onClose={() => setIsOpen(false)}
        project={project}
        onSaved={() => {
          setIsOpen(false);
          router.refresh();
        }}
      />
    </>
  );
}
