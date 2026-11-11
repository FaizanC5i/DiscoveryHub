import type { FormErrors } from "@/hooks/useForm";
import type {
  ForgotPasswordValues,
  LoginValues,
  ResetPasswordValues,
  SignUpValues,
} from "../types/auth";

/*
 * Client-side validation gives instant feedback. It is NOT a security boundary:
 * the backend repeats every rule (backend/app/schemas/auth.py), and the backend
 * is the one that decides. Keep these rules identical to the backend's, so a
 * form that passes here does not fail with a surprise from the server.
 */

export const PASSWORD_MIN_LENGTH = 8;
export const PASSWORD_MAX_LENGTH = 128;
export const NAME_MIN_LENGTH = 2;

const EMAIL_PATTERN = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
const HAS_LETTER = /[A-Za-z]/;
const HAS_DIGIT = /[0-9]/;

export function validateEmail(email: string): string | undefined {
  const trimmed = email.trim();
  if (!trimmed) {
    return "Enter your email address.";
  }
  if (!EMAIL_PATTERN.test(trimmed)) {
    return "Enter a valid email address.";
  }
  return undefined;
}

/**
 * New passwords (sign-up and reset) need length, a letter and a digit.
 * Returns the first problem found, or undefined when the password is acceptable.
 */
export function validateNewPassword(password: string): string | undefined {
  if (!password) {
    return "Create a password.";
  }
  if (password.length < PASSWORD_MIN_LENGTH) {
    return `Password must be at least ${PASSWORD_MIN_LENGTH} characters.`;
  }
  if (password.length > PASSWORD_MAX_LENGTH) {
    return `Password must be at most ${PASSWORD_MAX_LENGTH} characters.`;
  }
  if (!HAS_LETTER.test(password) || !HAS_DIGIT.test(password)) {
    return "Password must include at least one letter and one number.";
  }
  return undefined;
}

export function validateLogin(values: LoginValues): FormErrors<LoginValues> {
  const errors: FormErrors<LoginValues> = {};

  const emailError = validateEmail(values.email);
  if (emailError) {
    errors.email = emailError;
  }

  // No strength check on login. Old accounts must still be able to sign in.
  if (!values.password) {
    errors.password = "Enter your password.";
  }

  return errors;
}

export function validateSignUp(values: SignUpValues): FormErrors<SignUpValues> {
  const errors: FormErrors<SignUpValues> = {};

  const name = values.name.trim();
  if (!name) {
    errors.name = "Enter your name.";
  } else if (name.length < NAME_MIN_LENGTH) {
    errors.name = `Name must be at least ${NAME_MIN_LENGTH} characters.`;
  }

  const emailError = validateEmail(values.email);
  if (emailError) {
    errors.email = emailError;
  }

  const passwordError = validateNewPassword(values.password);
  if (passwordError) {
    errors.password = passwordError;
  }

  if (!values.confirmPassword) {
    errors.confirmPassword = "Confirm your password.";
  } else if (values.confirmPassword !== values.password) {
    errors.confirmPassword = "Passwords do not match.";
  }

  return errors;
}

export function validateForgotPassword(values: ForgotPasswordValues): FormErrors<ForgotPasswordValues> {
  const emailError = validateEmail(values.email);
  return emailError ? { email: emailError } : {};
}

export function validateResetPassword(values: ResetPasswordValues): FormErrors<ResetPasswordValues> {
  const errors: FormErrors<ResetPasswordValues> = {};

  const passwordError = validateNewPassword(values.password);
  if (passwordError) {
    errors.password = passwordError;
  }

  if (!values.confirmPassword) {
    errors.confirmPassword = "Confirm your new password.";
  } else if (values.confirmPassword !== values.password) {
    errors.confirmPassword = "Passwords do not match.";
  }

  return errors;
}
