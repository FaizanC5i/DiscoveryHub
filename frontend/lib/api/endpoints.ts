/**
 * Backend API paths, in one place. Services import these instead of writing
 * "/api/auth/..." strings, so a backend path change touches one file.
 */
export const API_PATHS = {
  auth: {
    signUp: "/api/auth/signup",
    login: "/api/auth/login",
    logout: "/api/auth/logout",
    refresh: "/api/auth/refresh",
    me: "/api/auth/me",
    forgotPassword: "/api/auth/forgot-password",
    resetPassword: "/api/auth/reset-password",
  },
  projects: {
    list: "/api/projects",
    detail: (projectId: number | string) => `/api/projects/${projectId}`,
  },
    sources: {
    list: (projectId: number | string) => `/api/projects/${projectId}/sources`,
    detail: (projectId: number | string, sourceId: number | string) =>
      `/api/projects/${projectId}/sources/${sourceId}`,
    reprocess: (projectId: number | string, sourceId: number | string) =>
      `/api/projects/${projectId}/sources/${sourceId}/reprocess`,
  },
  notes: {
    list: (projectId: number | string) => `/api/projects/${projectId}/notes`,
    detail: (projectId: number | string, noteId: number | string) =>
      `/api/projects/${projectId}/notes/${noteId}`,
  },
    userDiscovery: {
    overview: (projectId: number | string) => `/api/projects/${projectId}/user-discovery`,
    runs: (projectId: number | string) => `/api/projects/${projectId}/user-discovery/runs`,
    regenerate: (projectId: number | string, checkpointId: number | string) =>
      `/api/projects/${projectId}/user-discovery/checkpoints/${checkpointId}/regenerate`,
    approve: (projectId: number | string, proposalId: number | string) =>
      `/api/projects/${projectId}/user-discovery/proposals/${proposalId}/approve`,
  },
} as const;
