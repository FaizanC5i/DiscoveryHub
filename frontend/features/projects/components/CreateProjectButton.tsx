"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";
import { PlusIcon } from "@/components/icons";
import { Button } from "@/components/ui/Button";
import { ROUTES } from "@/lib/constants";
import { ProjectFormModal } from "./ProjectFormModal";

interface CreateProjectButtonProps {
  label?: string;
  className?: string;
}

/**
 * Opens the create-project dialog. After a successful save, the user lands on the
 * new project's overview page, so every detail they entered is visible there.
 */
export function CreateProjectButton({ label = "Create New Project", className }: CreateProjectButtonProps) {
  const router = useRouter();
  const [isOpen, setIsOpen] = useState(false);

  return (
    <>
      <Button className={className} onClick={() => setIsOpen(true)}>
        <PlusIcon className="size-4" />
        {label}
      </Button>
      <ProjectFormModal
        open={isOpen}
        onClose={() => setIsOpen(false)}
        onSaved={(project) => {
          // Close first: Next.js can keep this page mounted (hidden) after navigating away,
          // and a dialog left open here would reappear when the user comes back to the dashboard.
          setIsOpen(false);
          router.push(ROUTES.projectDetail(project.id));
        }}
      />
    </>
  );
}
