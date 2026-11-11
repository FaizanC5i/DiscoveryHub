"use client";

import { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useForm } from "@/hooks/useForm";
import { ArrowRightIcon } from "@/components/icons";
import { Alert } from "@/components/ui/Alert";
import { Button } from "@/components/ui/Button";
import { FormField } from "@/components/ui/FormField";
import { Input } from "@/components/ui/Input";
import { PasswordInput } from "@/components/ui/PasswordInput";
import { isApiError } from "@/lib/api/client";
import { ROUTES } from "@/lib/constants";
import type { SignUpValues } from "../types/auth";
import { authService } from "../services/authService";
import { PASSWORD_MIN_LENGTH, validateSignUp } from "../utils/validation";
import { AuthFooterPrompt } from "./AuthFooterPrompt";
import { AuthHeading } from "./AuthHeading";

interface SignUpFormProps {
  /** Pre-fills the email when the visitor came from a "no account found" sign-in. */
  initialEmail?: string;
}

export function SignUpForm({ initialEmail = "" }: SignUpFormProps) {
  const router = useRouter();
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
    <>
      <AuthHeading
        eyebrow="Get started"
        title="Create your account"
        description="Start turning product ideas into build-ready requirements."
      />

      <form method="post" noValidate onSubmit={handleSubmit} className="mt-10 flex flex-col gap-6">
        {submitError ? <Alert>{submitError}</Alert> : null}

        {takenEmail ? (
          <Alert>
            An account already exists for this email.{" "}
            <Link href={ROUTES.login} className="font-semibold text-fg-brand hover:text-fg-brand-strong">
              Sign in instead
            </Link>
          </Alert>
        ) : null}

        <FormField label="Full name" error={errors.name}>
          {(controlProps) => (
            <Input
              {...controlProps}
              type="text"
              name="name"
              autoComplete="name"
              placeholder="Alex Kim"
              value={values.name}
              onChange={handleChange}
              onBlur={handleBlur}
            />
          )}
        </FormField>

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

        <FormField label="Confirm password" error={errors.confirmPassword}>
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
          Create account
          <ArrowRightIcon className="size-5" />
        </Button>
      </form>

      <div className="mt-10">
        <AuthFooterPrompt prompt="Already have an account?" linkLabel="Sign in" href={ROUTES.login} />
      </div>
    </>
  );
}
