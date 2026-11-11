"use client";

import { GoogleIcon } from "@/components/icons";
import { Button } from "@/components/ui/Button";

interface SocialAuthButtonProps {
  onClick: () => void;
  loading?: boolean;
  disabled?: boolean;
}

export function SocialAuthButton({ onClick, loading = false, disabled = false }: SocialAuthButtonProps) {
  return (
    <Button
      variant="outline"
      fullWidth
      onClick={onClick}
      loading={loading}
      disabled={disabled}
    >
      {loading ? null : <GoogleIcon className="size-5 text-fg-secondary" />}
      Sign in with Google
    </Button>
  );
}
