"use client";

import { useState, useEffect } from "react";
import { LucideIcon } from "lucide-react";

interface MaterialIconWithFallbackProps {
  name: string;
  fallback: LucideIcon;
  className?: string;
  fillFallback?: boolean;
}

export function MaterialIconWithFallback({
  name,
  fallback: Fallback,
  className,
  fillFallback = false,
}: MaterialIconWithFallbackProps) {
  const [fontsLoaded, setFontsLoaded] = useState(false);

  useEffect(() => {
    // Check if the font is already loaded
    if (document.fonts.check("20px 'Material Symbols Outlined'")) {
      setFontsLoaded(true);
      return;
    }

    // Otherwise wait for it
    document.fonts.load("20px 'Material Symbols Outlined'").then(() => {
      setFontsLoaded(true);
    });
  }, []);

  if (!fontsLoaded) {
    return (
      <Fallback
        className={className}
        size={20}
        fill={fillFallback ? "currentColor" : "none"}
      />
    );
  }

  return (
    <span
      className={`material-symbols-outlined leading-none ${className || ""}`}
      style={{ fontSize: 20, fontVariationSettings: "'FILL' 1" }}
    >
      {name}
    </span>
  );
}
