"use client";

import { useState } from "react";
import { cn } from "@/lib/cn";
import { EyeIcon, EyeOffIcon } from "@/components/icons";
import { Input, type InputProps } from "./Input";

/** Password field with a show/hide toggle. */
export function PasswordInput({ className, ...props }: Omit<InputProps, "type">) {
  const [isVisible, setIsVisible] = useState(false);

  return (
    <div className="relative">
      <Input
        {...props}
        type={isVisible ? "text" : "password"}
        className={cn("pr-11", className)}
      />
      <button
        type="button"
        onClick={() => setIsVisible((previous) => !previous)}
        aria-label={isVisible ? "Hide password" : "Show password"}
        aria-pressed={isVisible}
        className="absolute inset-y-0 right-0 flex w-11 items-center justify-center text-icon hover:text-icon-strong focus-visible:outline-2 focus-visible:outline-border-brand-strong rounded-control"
      >
        {isVisible ? <EyeOffIcon className="size-5" /> : <EyeIcon className="size-5" />}
      </button>
    </div>
  );
}
