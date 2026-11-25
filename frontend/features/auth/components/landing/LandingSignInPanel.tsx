"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState, type Ref } from "react";
import { useForm } from "@/hooks/useForm";
import { isApiError } from "@/lib/api/client";
import { ROUTES } from "@/lib/constants";
import { authService } from "../../services/authService";
import type { LoginValues } from "../../types/auth";
import { validateLogin } from "../../utils/validation";
import { LandingArrow } from "./LandingArrow";
import { LandingBrand } from "./LandingBrand";

interface LandingSignInPanelProps {
  onBack: () => void;
  onSwitchToSignUp: (email: string) => void;
  emailInputRef?: Ref<HTMLInputElement>;
}

/**
 * Sign-in panel in the landing design. Same behaviour as LoginForm: validation,
 * authService.login, "no account" prompt, then the dashboard. The Microsoft button is a
 * placeholder until the backend supports it (the Microsoft logo colours are the brand's own).
 */
export function LandingSignInPanel({ onBack, onSwitchToSignUp, emailInputRef }: LandingSignInPanelProps) {
  const router = useRouter();
  const [showPassword, setShowPassword] = useState(false);
  const [ssoMessage, setSsoMessage] = useState<string | null>(null);
  /** Set when the email has no account: show a "Create an account" prompt instead of an error. */
  const [unknownEmail, setUnknownEmail] = useState<string | null>(null);

  const { values, errors, handleChange, handleBlur, handleSubmit, isSubmitting, submitError } =
    useForm<LoginValues>({
      initialValues: { email: "", password: "" },
      validate: validateLogin,
      onSubmit: async (submittedValues) => {
        setUnknownEmail(null);
        try {
          await authService.login(submittedValues);
        } catch (error) {
          if (isApiError(error, "ACCOUNT_NOT_FOUND")) {
            setUnknownEmail(submittedValues.email);
            return;
          }
          throw error;
        }
        router.push(ROUTES.dashboard);
      },
    });

  // PLACEHOLDER: the backend has no Microsoft sign-in yet. Replace with the real call when it does.
  function handleMicrosoftSignIn() {
    setSsoMessage("Microsoft sign-in is not available yet. Please sign in with your email and password.");
  }

  return (
    <section className="dhl-signin-view" aria-labelledby="dhl-signin-title">
      <div className="dhl-signin-panel">
        <button className="dhl-close-button" type="button" aria-label="Close sign in" onClick={onBack}>
          <svg viewBox="0 0 16 16" width="14" height="14" aria-hidden="true">
            <path d="M3 3l10 10M13 3L3 13" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" fill="none" />
          </svg>
        </button>

        <button className="dhl-brand-button" type="button" onClick={onBack} aria-label="Back to Discovery Hub home">
          <LandingBrand compact />
        </button>

        <div className="dhl-signin-panel__intro">
          <p className="dhl-eyebrow">WELCOME BACK</p>
          <h1 id="dhl-signin-title">Sign in to Discovery Hub</h1>
          <p className="dhl-subtitle">AI-powered discovery for enterprise engagements</p>
        </div>

        <form method="post" noValidate onSubmit={handleSubmit}>
          {submitError ? (
            <p role="alert" className="dhl-alert">
              {submitError}
            </p>
          ) : null}

          {unknownEmail ? (
            <p role="alert" className="dhl-alert">
              No account exists for {unknownEmail}.{" "}
              <button type="button" className="dhl-link-button" onClick={() => onSwitchToSignUp(unknownEmail)}>
                Create an account
              </button>
            </p>
          ) : null}

          <label htmlFor="dhl-email">Email address</label>
          <input
            ref={emailInputRef}
            id="dhl-email"
            name="email"
            type="email"
            autoComplete="email"
            placeholder="you@company.com"
            value={values.email}
            onChange={handleChange}
            onBlur={handleBlur}
            aria-invalid={errors.email ? true : undefined}
            aria-describedby={errors.email ? "dhl-email-error" : undefined}
          />
          {errors.email ? (
            <p id="dhl-email-error" className="dhl-field-error">
              {errors.email}
            </p>
          ) : null}

          <div className="dhl-password-label">
            <label htmlFor="dhl-password">Password</label>
            <Link href={ROUTES.forgotPassword}>Forgot password?</Link>
          </div>
          <div className="dhl-password-field">
            <input
              id="dhl-password"
              name="password"
              type={showPassword ? "text" : "password"}
              placeholder="Enter your password"
              autoComplete="current-password"
              value={values.password}
              onChange={handleChange}
              onBlur={handleBlur}
              aria-invalid={errors.password ? true : undefined}
              aria-describedby={errors.password ? "dhl-password-error" : undefined}
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
            <p id="dhl-password-error" className="dhl-field-error">
              {errors.password}
            </p>
          ) : null}

          <button className="dhl-submit-button" type="submit" disabled={isSubmitting} aria-busy={isSubmitting || undefined}>
            {isSubmitting ? "Signing in…" : "Sign In"} <LandingArrow large />
          </button>

          <div className="dhl-divider">
            <span>OR CONTINUE WITH</span>
          </div>

          {ssoMessage ? (
            <p role="status" className="dhl-notice">
              {ssoMessage}
            </p>
          ) : null}

          <button className="dhl-google-button" type="button" onClick={handleMicrosoftSignIn} disabled={isSubmitting}>
            <svg viewBox="0 0 21 21" width="20" height="20" aria-hidden="true">
              <rect x="1" y="1" width="9" height="9" fill="#F25022" />
              <rect x="11" y="1" width="9" height="9" fill="#7FBA00" />
              <rect x="1" y="11" width="9" height="9" fill="#00A4EF" />
              <rect x="11" y="11" width="9" height="9" fill="#FFB900" />
            </svg>
            Sign in with Microsoft
          </button>

          <p className="dhl-request-access">
            Don&apos;t have access?{" "}
            <button type="button" className="dhl-link-button" onClick={() => onSwitchToSignUp(values.email)}>
              Request access
            </button>
          </p>
        </form>
      </div>
    </section>
  );
}
