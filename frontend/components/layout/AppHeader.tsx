import { SettingsIcon } from "@/components/icons";
import { Logo } from "@/components/brand/Logo";
import { Avatar } from "@/components/ui/Avatar";
import { Button } from "@/components/ui/Button";
import { LogoutButton } from "@/features/auth/components/LogoutButton";
import { cn } from "@/lib/cn";
import type { User } from "@/types/user";

interface AppHeaderProps {
  user: User;
  /** Centered page title, shown from the md breakpoint up. */
  title?: string;
  /** "contained" matches the page content width; "full" spans the viewport. */
  width?: "contained" | "full";
}

export function AppHeader({ user, title, width = "contained" }: AppHeaderProps) {
  return (
    <header className="sticky top-0 z-10 border-b border-border-subtle bg-surface">
      <div
        className={cn(
          "mx-auto grid h-16 w-full grid-cols-[1fr_auto_1fr] items-center gap-4 px-4 sm:px-6 lg:px-8",
          width === "contained" && "max-w-5xl",
        )}
      >
        <Logo />

        <p className="hidden max-w-[32rem] truncate text-title-small font-semibold text-fg md:block">
          {title}
        </p>

        <div className="col-start-3 flex items-center justify-end gap-3">
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