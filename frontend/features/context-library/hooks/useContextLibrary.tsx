"use client";

import { createContext, useCallback, useContext, useMemo, useState, type ReactNode } from "react";

interface ContextLibraryState {
  isOpen: boolean;
  toggle: () => void;
  close: () => void;
}

const ContextLibraryContext = createContext<ContextLibraryState | null>(null);

export function ContextLibraryProvider({ children }: { children: ReactNode }) {
  const [isOpen, setIsOpen] = useState(true);
  const toggle = useCallback(() => setIsOpen((previous) => !previous), []);
  const close = useCallback(() => setIsOpen(false), []);
  const value = useMemo(() => ({ isOpen, toggle, close }), [isOpen, toggle, close]);

  return <ContextLibraryContext.Provider value={value}>{children}</ContextLibraryContext.Provider>;
}

export function useContextLibrary(): ContextLibraryState {
  const value = useContext(ContextLibraryContext);
  if (!value) {
    throw new Error("useContextLibrary must be used inside ContextLibraryProvider");
  }
  return value;
}