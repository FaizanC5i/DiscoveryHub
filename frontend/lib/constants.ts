export const APP_NAME = "Discovery Hub";

export const COPYRIGHT_TEXT = "© 2026 C5i (Course5 Intelligence)";

/**
 * Page routes. Components link through these constants so a route can be renamed
 * in one place. Add new routes here instead of writing path strings in components.
 */
export const ROUTES = {
  login: "/login",
  signup: "/signup",
  forgotPassword: "/forgot-password",
  resetPassword: "/reset-password",
  dashboard: "/dashboard",
  exports: "/exports",
  momAssistant: "/mom-assistant",
  /** Project overview page. Accepts the numeric project id from the API. */
  projectDetail: (projectId: number | string) => `/projects/${projectId}/overview`,
    /** A tab inside a project, such as "overview". */
  projectSection: (projectId: number | string, segment: string) =>
    `/projects/${projectId}/${segment}`,
} as const;

/**
 * Names of the session cookies set by the FastAPI backend.
 * Must match backend/app/core/cookies.py. The Next.js proxy and server code read
 * these names, so keep them identical on both sides.
 */
export const AUTH_COOKIES = {
  access: "access_token",
  refresh: "refresh_token",
} as const;
