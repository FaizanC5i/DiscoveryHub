import { apiRequest, ApiError } from "@/lib/api/client";
import { API_PATHS } from "@/lib/api/endpoints";
import type { User } from "@/types/user";
import type {
  AuthSession,
  ForgotPasswordValues,
  LoginValues,
  ResetPasswordValues,
  SignUpValues,
} from "../types/auth";

/**
 * Auth service boundary. Components depend only on this interface, so they do
 * not change when the implementation changes.
 *
 * Two implementations sit behind it:
 *   - apiAuthService:  calls the FastAPI backend (the default).
 *   - mockAuthService: returns canned data, for working on UI without a backend.
 *     Enable it with NEXT_PUBLIC_USE_MOCK_AUTH=true in .env.local.
 *
 * This file is for code that runs in the browser. Server code that needs the
 * current user reads it from features/auth/services/currentUser.ts instead,
 * because only the server can see the request's cookies.
 */
export interface AuthService {
  signUp(values: SignUpValues): Promise<AuthSession>;
  login(values: LoginValues): Promise<AuthSession>;
  signInWithGoogle(): Promise<AuthSession>;
  logout(): Promise<void>;
  forgotPassword(values: ForgotPasswordValues): Promise<void>;
  resetPassword(token: string, values: ResetPasswordValues): Promise<void>;
}

/** Mock user. Also used by the server-side mock in currentUser.ts. */
export const MOCK_USER: User = {
  id: 1,
  name: "Alex Kim",
  email: "alex@c5i.ai",
};

const mockAuthService: AuthService = {
  async signUp({ name, email }) {
    return { user: { id: 2, name: name.trim(), email: email.trim().toLowerCase() } };
  },

  async login({ email }) {
    return { user: { ...MOCK_USER, email: email.trim().toLowerCase() } };
  },

  async signInWithGoogle() {
    return { user: MOCK_USER };
  },

  async logout() {
    // Nothing to clear: the mock keeps no session.
  },

  async forgotPassword() {
    // Mock always succeeds, matching the real service's generic response.
  },

  async resetPassword() {
    // Mock always succeeds.
  },
};

const apiAuthService: AuthService = {
  async signUp({ name, email, password }) {
    const user = await apiRequest<User>(API_PATHS.auth.signUp, {
      method: "POST",
      body: JSON.stringify({ name, email, password }),
    });
    return { user };
  },

  async login({ email, password }) {
    const user = await apiRequest<User>(API_PATHS.auth.login, {
      method: "POST",
      body: JSON.stringify({ email, password }),
    });
    return { user };
  },

  async signInWithGoogle() {
    // The backend has no Google sign-in yet. Fail clearly instead of pretending.
    throw new ApiError("Google sign-in is not available yet.", 501, "NOT_IMPLEMENTED");
  },

  async logout() {
    await apiRequest(API_PATHS.auth.logout, { method: "POST" });
  },

  async forgotPassword({ email }) {
    await apiRequest(API_PATHS.auth.forgotPassword, {
      method: "POST",
      body: JSON.stringify({ email }),
    });
  },

  async resetPassword(token, { password }) {
    await apiRequest(API_PATHS.auth.resetPassword, {
      method: "POST",
      body: JSON.stringify({ token, password }),
    });
  },
};

export const USE_MOCK_AUTH = process.env.NEXT_PUBLIC_USE_MOCK_AUTH === "true";

/** The one instance components import. Chosen once, at build time, from the environment. */
export const authService: AuthService = USE_MOCK_AUTH ? mockAuthService : apiAuthService;
