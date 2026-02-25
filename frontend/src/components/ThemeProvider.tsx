"use client";

import { useEffect } from "react";
import { useProjectStore } from "@/lib/store";

export function ThemeProvider({ children }: { children: React.ReactNode }) {
  const uiTheme = useProjectStore((s) => s.uiTheme);

  useEffect(() => {
    document.documentElement.classList.toggle("dark", uiTheme === "dark");
  }, [uiTheme]);

  return <>{children}</>;
}
