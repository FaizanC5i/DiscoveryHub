import type { SVGProps } from "react";

/** Small line icons for the Discovery Hub page. They take the text colour. */
function Icon({ children, ...props }: SVGProps<SVGSVGElement>) {
  return (
    <svg
      width="16"
      height="16"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth={2}
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
      {...props}
    >
      {children}
    </svg>
  );
}

export const ArrowRightIcon = () => <Icon><path d="M5 12h14M13 6l6 6-6 6" /></Icon>;
export const ChevronLeftIcon = () => <Icon><path d="M15 18l-6-6 6-6" /></Icon>;
export const CloseIcon = () => <Icon><path d="M18 6L6 18M6 6l12 12" /></Icon>;
export const DownloadIcon = () => <Icon><path d="M12 4v12M6 10l6 6 6-6M5 20h14" /></Icon>;
export const InfoIcon = () => <Icon><circle cx="12" cy="12" r="9" /><path d="M12 16v-4M12 8h.01" /></Icon>;
export const PanelIcon = () => <Icon><rect x="3" y="4" width="18" height="16" rx="2" /><path d="M15 4v16" /></Icon>;
export const PlusIcon = () => <Icon><path d="M12 5v14M5 12h14" /></Icon>;
export const SearchIcon = () => <Icon><circle cx="11" cy="11" r="7" /><path d="M20 20l-3.5-3.5" /></Icon>;
export const SettingsIcon = () => (
  <Icon>
    <circle cx="12" cy="12" r="3" />
    <path d="M19.4 15a1.7 1.7 0 0 0 .3 1.8l.1.1a2 2 0 1 1-2.8 2.8l-.1-.1a1.7 1.7 0 0 0-1.8-.3 1.7 1.7 0 0 0-1 1.5V21a2 2 0 1 1-4 0v-.1a1.7 1.7 0 0 0-1.1-1.5 1.7 1.7 0 0 0-1.8.3l-.1.1a2 2 0 1 1-2.8-2.8l.1-.1a1.7 1.7 0 0 0 .3-1.8 1.7 1.7 0 0 0-1.5-1H3a2 2 0 1 1 0-4h.1a1.7 1.7 0 0 0 1.5-1.1 1.7 1.7 0 0 0-.3-1.8l-.1-.1a2 2 0 1 1 2.8-2.8l.1.1a1.7 1.7 0 0 0 1.8.3H9a1.7 1.7 0 0 0 1-1.5V3a2 2 0 1 1 4 0v.1a1.7 1.7 0 0 0 1 1.5 1.7 1.7 0 0 0 1.8-.3l.1-.1a2 2 0 1 1 2.8 2.8l-.1.1a1.7 1.7 0 0 0-.3 1.8V9a1.7 1.7 0 0 0 1.5 1H21a2 2 0 1 1 0 4h-.1a1.7 1.7 0 0 0-1.5 1z" />
  </Icon>
);