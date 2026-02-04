/**
 * Utility functions.
 */

import { clsx, type ClassValue } from "clsx";

export function cn(...inputs: ClassValue[]): string {
  return clsx(inputs);
}

export function formatDate(dateString: string): string {
  const date = new Date(dateString);
  return date.toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

export function getLanguageFromPath(path: string): string {
  const ext = path.split(".").pop()?.toLowerCase() || "";
  const langMap: Record<string, string> = {
    ts: "typescript",
    tsx: "tsx",
    js: "javascript",
    jsx: "jsx",
    py: "python",
    json: "json",
    md: "markdown",
    css: "css",
    scss: "scss",
    html: "html",
    yaml: "yaml",
    yml: "yaml",
    toml: "toml",
    sql: "sql",
    sh: "bash",
    bash: "bash",
    go: "go",
    rs: "rust",
    java: "java",
  };
  return langMap[ext] || "text";
}

export function getFileIcon(language: string): string {
  const iconMap: Record<string, string> = {
    typescript: "📘",
    tsx: "⚛️",
    javascript: "📙",
    jsx: "⚛️",
    python: "🐍",
    json: "📋",
    markdown: "📝",
    css: "🎨",
    html: "🌐",
    yaml: "⚙️",
    sql: "🗄️",
    bash: "💻",
    go: "🔷",
    rust: "🦀",
  };
  return iconMap[language] || "📄";
}

export function truncate(str: string, length: number): string {
  if (str.length <= length) return str;
  return str.slice(0, length) + "...";
}

export function getAgentColor(agent: string): string {
  const colors: Record<string, string> = {
    manager: "text-white",
    architect: "text-gray-300",
    engineer: "text-gray-400",
    qa: "text-gray-500",
  };
  return colors[agent.toLowerCase()] || "text-foreground-muted";
}

export function getAgentBgColor(agent: string): string {
  const colors: Record<string, string> = {
    manager: "bg-white/10",
    architect: "bg-gray-300/10",
    engineer: "bg-gray-400/10",
    qa: "bg-gray-500/10",
  };
  return colors[agent.toLowerCase()] || "bg-background-tertiary";
}

export function getSeverityColor(severity: string): string {
  const colors: Record<string, string> = {
    error: "text-error",
    warning: "text-warning",
    info: "text-gray-400",
  };
  return colors[severity.toLowerCase()] || "text-foreground-muted";
}

export function getPriorityColor(priority: string): string {
  const colors: Record<string, string> = {
    high: "text-error",
    medium: "text-warning",
    low: "text-success",
  };
  return colors[priority.toLowerCase()] || "text-foreground-muted";
}
