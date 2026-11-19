/**
 * A project as returned by the backend (GET/POST/PATCH /api/projects).
 *
 * Field names match the JSON exactly (snake_case), so responses can be used
 * without a conversion step. Dates are "YYYY-MM-DD" strings or null. Timestamps
 * are ISO 8601 strings with a UTC offset.
 */
export interface Project {
  id: number;
  name: string;
  description: string | null;
  owner_id: number;
  owner_name: string;
  start_date: string | null;
  end_date: string | null;
  created_at: string;
  updated_at: string;
}

/** What the create and edit forms send to the backend. Null clears an optional field. */
export interface ProjectInput {
  name: string;
  description: string | null;
  start_date: string | null;
  end_date: string | null;
}
