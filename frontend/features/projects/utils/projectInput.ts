import type { Project, ProjectInput } from "@/types/project";
import type { ProjectFormValues } from "../types/projectForm";

/** Turns the form's text values into the API shape. Blank optional fields become null. */
export function toProjectInput(values: ProjectFormValues): ProjectInput {
  return {
    name: values.name.trim(),
    description: values.description.trim() || null,
    start_date: values.startDate || null,
    end_date: values.endDate || null,
  };
}

/** Fills the edit form from a saved project. Null becomes an empty string for the inputs. */
export function toFormValues(project: Project): ProjectFormValues {
  return {
    name: project.name,
    description: project.description ?? "",
    startDate: project.start_date ?? "",
    endDate: project.end_date ?? "",
  };
}
