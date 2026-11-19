"use client";

import { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useForm } from "@/hooks/useForm";
import { ArrowRightIcon } from "@/components/icons";
import { Alert } from "@/components/ui/Alert";
import { Button } from "@/components/ui/Button";
import { FormField } from "@/components/ui/FormField";
import { PasswordInput } from "@/components/ui/PasswordInput";
import { PASSWORD_MIN_LENGTH, validateResetPassword } from "../utils/validation";
import { ROUTES } from "@/lib/constants";
import type { ResetPasswordValues } from "../types/auth";
import { authService } from "../services/authService";
import { AuthFooterPrompt } from "./AuthFooterPrompt";
import { AuthHeading } from "./AuthHeading";

interface ResetPasswordFormProps {
  /** The one-time token from the emailed link. Empty when the link was opened without one. */
  token: string;
}

/**
 * Sets a new password using the token from the reset email.
 *
 * The token itself is never shown or stored in the browser. It is sent once to
 * the backend, which checks it and marks it as used.
 */
export function ResetPasswordForm({ token }: ResetPasswordFormProps) {
  const router = useRouter();
  const [isDone, setIsDone] = useState(false);

  const { values, errors, handleChange, handleBlur, handleSubmit, isSubmitting, submitError } =
    useForm<ResetPasswordValues>({
      initialValues: { password: "", confirmPassword: "" },
      validate: validateResetPassword,
      onSubmit: async (submittedValues) => {
        await authService.resetPassword(token, submittedValues);
        setIsDone(true);
      },
    });

  if (!token) {
    return (
      <>
        <AuthHeading
          eyebrow="Reset password"
          title="This link is incomplete"
          description="The reset link is missing its token. Request a new one to continue."
        />
        <div className="mt-10 flex flex-col gap-6">
          <Button fullWidth onClick={() => router.push(ROUTES.forgotPassword)}>
            Request a new link
            <ArrowRightIcon className="size-5" />
          </Button>
        </div>
      </>
    );
  }

  if (isDone) {
    return (
      <>
        <AuthHeading
          eyebrow="Password updated"
          title="You can now sign in"
          description="Your password has been changed. For your security, you have been signed out on every device."
        />
        <div className="mt-10 flex flex-col gap-6">
          <Button fullWidth onClick={() => router.push(ROUTES.login)}>
            Go to sign in
            <ArrowRightIcon className="size-5" />
          </Button>
        </div>
      </>
    );
  }

  return (
    <>
      <AuthHeading
        eyebrow="Reset password"
        title="Choose a new password"
        description="Pick a password you have not used on this account before."
      />

      <form method="post" noValidate onSubmit={handleSubmit} className="mt-10 flex flex-col gap-6">
        {submitError ? (
          <Alert>
            {submitError}{" "}
            <Link href={ROUTES.forgotPassword} className="font-semibold text-fg-brand hover:text-fg-brand-strong">
              Request a new link
            </Link>
          </Alert>
        ) : null}

        <FormField
          label="New password"
          error={errors.password}
          hint={errors.password ? undefined : `At least ${PASSWORD_MIN_LENGTH} characters, with a letter and a number.`}
        >
          {(controlProps) => (
            <PasswordInput
              {...controlProps}
              name="password"
              autoComplete="new-password"
              value={values.password}
              onChange={handleChange}
              onBlur={handleBlur}
            />
          )}
        </FormField>

        <FormField label="Confirm new password" error={errors.confirmPassword}>
          {(controlProps) => (
            <PasswordInput
              {...controlProps}
              name="confirmPassword"
              autoComplete="new-password"
              value={values.confirmPassword}
              onChange={handleChange}
              onBlur={handleBlur}
            />
          )}
        </FormField>

        <Button type="submit" fullWidth loading={isSubmitting}>
          Update password
          <ArrowRightIcon className="size-5" />
        </Button>
      </form>

      <div className="mt-10">
        <AuthFooterPrompt prompt="Remembered it?" linkLabel="Back to sign in" href={ROUTES.login} />
      </div>
    </>
  );
}
