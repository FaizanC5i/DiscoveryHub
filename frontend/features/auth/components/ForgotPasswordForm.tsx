"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { useForm } from "@/hooks/useForm";
import { ArrowRightIcon } from "@/components/icons";
import { Alert } from "@/components/ui/Alert";
import { Button } from "@/components/ui/Button";
import { FormField } from "@/components/ui/FormField";
import { Input } from "@/components/ui/Input";
import { ROUTES } from "@/lib/constants";
import type { ForgotPasswordValues } from "../types/auth";
import { authService } from "../services/authService";
import { validateForgotPassword } from "../utils/validation";
import { AuthFooterPrompt } from "./AuthFooterPrompt";
import { AuthHeading } from "./AuthHeading";

/**
 * Asks for an email and requests a reset link.
 *
 * The confirmation text is the same whether or not the account exists. Showing
 * a different message would let anyone find out which emails are registered.
 */
export function ForgotPasswordForm() {
  const router = useRouter();
  const [isRequested, setIsRequested] = useState(false);

  const { values, errors, handleChange, handleBlur, handleSubmit, isSubmitting, submitError } =
    useForm<ForgotPasswordValues>({
      initialValues: { email: "" },
      validate: validateForgotPassword,
      onSubmit: async (submittedValues) => {
        await authService.forgotPassword(submittedValues);
        setIsRequested(true);
      },
    });

  if (isRequested) {
    return (
      <>
        <AuthHeading
          eyebrow="Check your inbox"
          title="Reset link on its way"
          description="If an account exists for that email, we have sent a link to reset your password. The link expires in 30 minutes."
        />
        <div className="mt-10 flex flex-col gap-6">
          <Button fullWidth onClick={() => router.push(ROUTES.login)}>
            Back to sign in
          </Button>
        </div>
      </>
    );
  }

  return (
    <>
      <AuthHeading
        eyebrow="Account recovery"
        title="Forgot your password?"
        description="Enter your email and we will send you a link to choose a new one."
      />

      <form method="post" noValidate onSubmit={handleSubmit} className="mt-10 flex flex-col gap-6">
        {submitError ? <Alert>{submitError}</Alert> : null}

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

        <Button type="submit" fullWidth loading={isSubmitting}>
          Send reset link
          <ArrowRightIcon className="size-5" />
        </Button>
      </form>

      <div className="mt-10">
        <AuthFooterPrompt prompt="Remembered it?" linkLabel="Back to sign in" href={ROUTES.login} />
      </div>
    </>
  );
}
