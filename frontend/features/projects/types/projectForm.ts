/**
 * Values held by the create and edit form. Everything is a string, because that
 * is what text inputs produce. toProjectInput() turns them into the API shape.
 */
export type ProjectFormValues = {
  name: string;
  description: string;
  startDate: string;
  endDate: string;
};
