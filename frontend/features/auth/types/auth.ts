import type { User } from "@/types/user";

export type LoginValues = {
  email: string;
  password: string;
};

export type SignUpValues = {
  name: string;
  email: string;
  password: string;
  confirmPassword: string;
};

export type ForgotPasswordValues = {
  email: string;
};

export type ResetPasswordValues = {
  password: string;
  confirmPassword: string;
};

/**
 * What a successful sign-in returns. The tokens are NOT here: they live in
 * HttpOnly cookies that the browser manages, and JavaScript never sees them.
 */
export interface AuthSession {
  user: User;
}
