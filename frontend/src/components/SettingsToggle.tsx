"use client";

import type { ReactNode } from "react";

interface SettingsToggleProps {
  /** Label shown on the left */
  label: string;
  /** Whether the toggle is on */
  checked: boolean;
  /** Called when the row is clicked */
  onToggle: () => void;
  /** Optional icon shown before the label */
  icon?: ReactNode;
}

export function SettingsToggle({
  label,
  checked,
  onToggle,
  icon,
}: SettingsToggleProps) {
  return (
    <button
      type="button"
      onClick={onToggle}
      className="w-full flex items-center justify-between gap-2 px-2.5 py-2.5 rounded-lg text-left transition-all duration-150 hover:bg-background-tertiary group"
    >
      <div
        className={`flex items-center min-w-0 ${icon ? "gap-2.5" : ""}`}
      >
        {icon}
        <span className="text-xs font-medium text-foreground-muted group-hover:text-foreground">
          {label}
        </span>
      </div>
      <div
        className={`relative w-8 h-[18px] rounded-full transition-colors duration-200 shrink-0 ${
          checked ? "bg-accent" : "bg-foreground-subtle/30"
        }`}
      >
        <div
          className={`absolute top-[2px] h-[14px] w-[14px] rounded-full shadow-sm transition-all duration-200 border ${
            checked
              ? "translate-x-[16px] bg-background-secondary border-white/20"
              : "translate-x-[2px] bg-background-secondary border-foreground-subtle/30"
          }`}
        />
      </div>
    </button>
  );
}
