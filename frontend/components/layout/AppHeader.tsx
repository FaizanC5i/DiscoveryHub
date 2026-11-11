import { SettingsIcon } from "@/components/icons";
import { Logo } from "@/components/brand/Logo";
import { Avatar } from "@/components/ui/Avatar";
import { Button } from "@/components/ui/Button";
import { LogoutButton } from "@/features/auth/components/LogoutButton";
import type { User } from "@/types/user";

interface AppHeaderProps {
  user: User;
}

export function AppHeader({ user }: AppHeaderProps) {
  return (
    <header className="sticky top-0 z-10 border-b border-border-subtle bg-surface">
      <div className="mx-auto flex h-16 w-full max-w-5xl items-center justify-between gap-4 px-4 sm:px-6 lg:px-8">
        <Logo />

        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2.5">
            <Avatar name={user.name} />
            <span className="hidden text-body-medium font-semibold text-fg sm:inline">{user.name}</span>
          </div>
          <Button variant="outline" size="sm" aria-label="Settings">
            <SettingsIcon className="size-4" />
            <span className="hidden sm:inline">Settings</span>
          </Button>
          <LogoutButton />
        </div>
      </div>
    </header>
  );
}
