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
} as const;
