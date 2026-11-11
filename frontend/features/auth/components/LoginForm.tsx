"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { useForm } from "@/hooks/useForm";
import { ArrowRightIcon } from "@/components/icons";
import { Alert } from "@/components/ui/Alert";
import { Button } from "@/components/ui/Button";
import { FormField } from "@/components/ui/FormField";
import { Input } from "@/components/ui/Input";
import { PasswordInput } from "@/components/ui/PasswordInput";
import { isApiError } from "@/lib/api/client";
import { ROUTES } from "@/lib/constants";
import type { LoginValues } from "../types/auth";
import { authService } from "../services/authService";
import { validateLogin } from "../utils/validation";
import { AuthDivider } from "./AuthDivider";
import { AuthFooterPrompt } from "./AuthFooterPrompt";
import { AuthHeading } from "./AuthHeading";
import { SocialAuthButton } from "./SocialAuthButton";

export function LoginForm() {
  const router = useRouter();
  const [isGoogleLoading, setIsGoogleLoading] = useState(false);
  const [googleError, setGoogleError] = useState<string | null>(null);
  /**
   * Set when the email has no account. We show a Sign Up prompt instead of a
   * generic error, because the user most likely just needs to register.
   */
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
            // Handled inline below, so swallow the error here instead of showing it twice.
            setUnknownEmail(submittedValues.email);
            return;
          }
          throw error;
        }
        router.push(ROUTES.dashboard);
      },
    });

  async function handleGoogleSignIn() {
    setIsGoogleLoading(true);
    setGoogleError(null);
    try {
      await authService.signInWithGoogle();
      router.push(ROUTES.dashboard);
    } catch (error) {
      setGoogleError(error instanceof Error ? error.message : "Google sign-in failed. Please try again.");
    } finally {
      setIsGoogleLoading(false);
    }
  }

  return (
    <>
      <AuthHeading
        eyebrow="Welcome back"
        title="Sign in to Discovery Hub"
        description="AI-powered requirements to development workflow"
      />

      <form method="post" noValidate onSubmit={handleSubmit} className="mt-10 flex flex-col gap-6">
        {submitError ? <Alert>{submitError}</Alert> : null}

        {unknownEmail ? (
          <Alert>
            No account exists for {unknownEmail}.{" "}
            <Link
              href={`${ROUTES.signup}?email=${encodeURIComponent(unknownEmail)}`}
              className="font-semibold text-fg-brand hover:text-fg-brand-strong"
            >
              Create an account
            </Link>
          </Alert>
        ) : null}

        <FormField label="Email address" error={errors.email}>
          {(controlProps) => (
            <Input
              {...controlProps}
              type="email"
              name="email"
              autoComplete="email"
              placeholder="you@company.com"
              value={values.email}
              onChange={handleChange}
              onBlur={handleBlur}
            />
          )}
        </FormField>

        <FormField
          label="Password"
          error={errors.password}
          labelAction={
            <Link href={ROUTES.forgotPassword} className="text-body-medium font-semibold text-fg-brand hover:text-fg-brand-strong">
              Forgot password?
            </Link>
          }
        >
          {(controlProps) => (
            <PasswordInput
              {...controlProps}
              name="password"
              autoComplete="current-password"
              value={values.password}
              onChange={handleChange}
              onBlur={handleBlur}
            />
          )}
        </FormField>

        <Button type="submit" fullWidth loading={isSubmitting}>
          Sign In
          <ArrowRightIcon className="size-5" />
        </Button>
      </form>

      <div className="mt-8 flex flex-col gap-6">
        <AuthDivider label="Or continue with" />

        {googleError ? <Alert>{googleError}</Alert> : null}

        <SocialAuthButton onClick={handleGoogleSignIn} loading={isGoogleLoading} disabled={isSubmitting} />
      </div>

      <div className="mt-10">
        <AuthFooterPrompt prompt="New to Discovery Hub?" linkLabel="Create an account" href={ROUTES.signup} />
      </div>
    </>
  );
}
