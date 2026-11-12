import type { FormErrors } from "@/hooks/useForm";
import type { ProjectFormValues } from "../types/projectForm";

/** Must match DESCRIPTION_MAX_LENGTH in backend/app/schemas/project.py. */
export const PROJECT_DESCRIPTION_MAX_LENGTH = 12000;
/**
 * Client-side checks for the project form, shown inline as the user types.
 *
 * Analogy: the spell-checker under the text box. It catches obvious slips before
 * the document is sent. The backend runs the same rules again, and that check
 * is the one that counts.
 */
export function validateProjectForm(values: ProjectFormValues): FormErrors<ProjectFormValues> {
  const errors: FormErrors<ProjectFormValues> = {};

  if (!values.name.trim()) {
    errors.name = "Enter a project name.";
  } else if (values.name.trim().length > 255) {
    errors.name = "Project name must be at most 255 characters.";
  }

  if (values.description.trim().length > PROJECT_DESCRIPTION_MAX_LENGTH) {
    errors.description = `Description must be at most ${PROJECT_DESCRIPTION_MAX_LENGTH.toLocaleString("en-US")} characters.`;
  }

  // Dates are "YYYY-MM-DD", so a plain string comparison gives the right order.
  if (values.startDate && values.endDate && values.endDate < values.startDate) {
    errors.endDate = "End date cannot be before the start date.";
  }

  return errors;
}
