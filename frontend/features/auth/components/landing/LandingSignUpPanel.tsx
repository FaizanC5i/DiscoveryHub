"use client";

import { useRouter } from "next/navigation";
import { useState, type Ref } from "react";
import { useForm } from "@/hooks/useForm";
import { isApiError } from "@/lib/api/client";
import { ROUTES } from "@/lib/constants";
import { authService } from "../../services/authService";
import type { SignUpValues } from "../../types/auth";
import { PASSWORD_MIN_LENGTH, validateSignUp } from "../../utils/validation";
import { LandingArrow } from "./LandingArrow";
import { LandingBrand } from "./LandingBrand";

interface LandingSignUpPanelProps {
  onBack: () => void;
  onSwitchToSignIn: () => void;
  /** Pre-fills the email when the visitor came from a "no account" sign-in. */
  initialEmail?: string;
  nameInputRef?: Ref<HTMLInputElement>;
}

/**
 * Sign-up panel in the landing design. Same behaviour as SignUpForm: validation,
 * authService.signUp, "already registered" prompt, then the dashboard.
 */
export function LandingSignUpPanel({ onBack, onSwitchToSignIn, initialEmail = "", nameInputRef }: LandingSignUpPanelProps) {
  const router = useRouter();
  const [showPassword, setShowPassword] = useState(false);
  /** Set when the email already has an account: show a "Sign in instead" prompt. */
  const [takenEmail, setTakenEmail] = useState<string | null>(null);

  const { values, errors, handleChange, handleBlur, handleSubmit, isSubmitting, submitError } =
    useForm<SignUpValues>({
      initialValues: { name: "", email: initialEmail, password: "", confirmPassword: "" },
      validate: validateSignUp,
      onSubmit: async (submittedValues) => {
        setTakenEmail(null);
        try {
          await authService.signUp(submittedValues);
        } catch (error) {
          if (isApiError(error, "EMAIL_TAKEN")) {
            setTakenEmail(submittedValues.email);
            return;
          }
          throw error;
        }
        router.push(ROUTES.dashboard);
      },
    });

  return (
    <section className="dhl-signin-view" aria-labelledby="dhl-signup-title">
      <div className="dhl-signin-panel">
        <button className="dhl-close-button" type="button" aria-label="Close sign up" onClick={onBack}>
          <svg viewBox="0 0 16 16" width="14" height="14" aria-hidden="true">
            <path d="M3 3l10 10M13 3L3 13" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" fill="none" />
          </svg>
        </button>

        <button className="dhl-brand-button" type="button" onClick={onBack} aria-label="Back to Discovery Hub home">
          <LandingBrand compact />
        </button>

        <div className="dhl-signin-panel__intro">
          <p className="dhl-eyebrow">GET STARTED</p>
          <h1 id="dhl-signup-title">Create your account</h1>
          <p className="dhl-subtitle">Start turning product ideas into build-ready requirements.</p>
        </div>

        <form method="post" noValidate onSubmit={handleSubmit}>
          {submitError ? (
            <p role="alert" className="dhl-alert">
              {submitError}
            </p>
          ) : null}

          {takenEmail ? (
            <p role="alert" className="dhl-alert">
              An account already exists for {takenEmail}.{" "}
              <button type="button" className="dhl-link-button" onClick={onSwitchToSignIn}>
                Sign in instead
              </button>
            </p>
          ) : null}

          <label htmlFor="dhl-name">Full name</label>
          <input
            ref={nameInputRef}
            id="dhl-name"
            name="name"
            type="text"
            autoComplete="name"
            placeholder="Alex Kim"
            value={values.name}
            onChange={handleChange}
            onBlur={handleBlur}
            aria-invalid={errors.name ? true : undefined}
            aria-describedby={errors.name ? "dhl-name-error" : undefined}
          />
          {errors.name ? (
            <p id="dhl-name-error" className="dhl-field-error">
              {errors.name}
            </p>
          ) : null}

          <label htmlFor="dhl-signup-email">Email address</label>
          <input
            id="dhl-signup-email"
            name="email"
            type="email"
            autoComplete="email"
            placeholder="you@company.com"
            value={values.email}
            onChange={handleChange}
            onBlur={handleBlur}
            aria-invalid={errors.email ? true : undefined}
            aria-describedby={errors.email ? "dhl-signup-email-error" : undefined}
          />
          {errors.email ? (
            <p id="dhl-signup-email-error" className="dhl-field-error">
              {errors.email}
            </p>
          ) : null}

          <label htmlFor="dhl-signup-password">Password</label>
          <div className="dhl-password-field">
            <input
              id="dhl-signup-password"
              name="password"
              type={showPassword ? "text" : "password"}
              placeholder="Create a password"
              autoComplete="new-password"
              value={values.password}
              onChange={handleChange}
              onBlur={handleBlur}
              aria-invalid={errors.password ? true : undefined}
              aria-describedby={errors.password ? "dhl-signup-password-error" : "dhl-signup-password-hint"}
            />
            <button
              type="button"
              onClick={() => setShowPassword((visible) => !visible)}
              aria-label={showPassword ? "Hide password" : "Show password"}
              aria-pressed={showPassword}
            >
              {showPassword ? "Hide" : "Show"}
            </button>
          </div>
          {errors.password ? (
            <p id="dhl-signup-password-error" className="dhl-field-error">
              {errors.password}
            </p>
          ) : (
            <p id="dhl-signup-password-hint" className="dhl-hint">
              At least {PASSWORD_MIN_LENGTH} characters, with a letter and a number.
            </p>
          )}

          <label htmlFor="dhl-confirm-password">Confirm password</label>
          <div className="dhl-password-field">
            <input
              id="dhl-confirm-password"
              name="confirmPassword"
              type={showPassword ? "text" : "password"}
              placeholder="Re-enter your password"
              autoComplete="new-password"
              value={values.confirmPassword}
              onChange={handleChange}
              onBlur={handleBlur}
              aria-invalid={errors.confirmPassword ? true : undefined}
              aria-describedby={errors.confirmPassword ? "dhl-confirm-password-error" : undefined}
            />
          </div>
          {errors.confirmPassword ? (
            <p id="dhl-confirm-password-error" className="dhl-field-error">
              {errors.confirmPassword}
            </p>
          ) : null}

          <button className="dhl-submit-button" type="submit" disabled={isSubmitting} aria-busy={isSubmitting || undefined}>
            {isSubmitting ? "Creating account…" : "Create Account"} <LandingArrow large />
          </button>

          <p className="dhl-request-access">
            Already have an account?{" "}
            <button type="button" className="dhl-link-button" onClick={onSwitchToSignIn}>
              Sign in
            </button>
          </p>
        </form>
      </div>
    </section>
  );
}
