"use client";

import { useProjectStore, getDefaultEditorThemeForUi } from "@/lib/store";
import { registerCustomThemes } from "@/lib/editorThemes";
import dynamic from "next/dynamic";
import { Copy, Check } from "lucide-react";
import { useState, useRef } from "react";

const MonacoEditor = dynamic(() => import("@monaco-editor/react"), {
  ssr: false,
}) as any;

export function CodeViewer() {
  const {
    selectedFile,
    fileContent,
    fileLanguage,
    generatedFiles,
    editorTheme,
    editorThemeAuto,
    uiTheme,
  } = useProjectStore();
  const effectiveTheme = editorThemeAuto
    ? getDefaultEditorThemeForUi(uiTheme)
    : editorTheme;
  const [copied, setCopied] = useState(false);
  const themesRegistered = useRef(false);

  // Try to get content from generated files if not loaded
  const content =
    fileContent ||
    generatedFiles.find((f) => f.file_path === selectedFile)?.file_content ||
    null;

  const language = fileLanguage || "plaintext";

  const handleCopy = async () => {
    if (content) {
      await navigator.clipboard.writeText(content);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  /** Register custom themes before Monaco mounts */
  const handleBeforeMount = (monaco: any) => {
    if (!themesRegistered.current) {
      registerCustomThemes(monaco);
      themesRegistered.current = true;
    }
  };

  if (!selectedFile) {
    return (
      <div className="flex-1 flex items-center justify-center text-foreground-muted">
        <div className="text-center">
          <p>Select a file to view its contents</p>
          <p className="text-sm text-foreground-subtle mt-1">
            Files are shown in the explorer on the left
          </p>
        </div>
      </div>
    );
  }

  if (!content) {
    return (
      <div className="flex-1 flex items-center justify-center text-foreground-muted">
        <div className="h-5 w-5 border-2 border-accent/30 border-t-accent rounded-full animate-spin" />
      </div>
    );
  }

  return (
    <div className="flex flex-col h-full w-full min-w-0 overflow-hidden">
      {/* File Header */}
      <div className="h-10 px-4 border-b border-border flex items-center justify-between shrink-0">
        <div className="flex items-center gap-2">
          <span className="text-sm font-medium text-foreground-muted">
            {selectedFile}
          </span>
          <span className="text-xs px-1.5 py-0.5 rounded bg-background-tertiary text-foreground-subtle">
            {language}
          </span>
        </div>
        <button
          onClick={handleCopy}
          className="p-1.5 rounded hover:bg-background-tertiary transition-colors"
          title="Copy to clipboard"
        >
          {copied ? (
            <Check className="h-4 w-4 text-success" />
          ) : (
            <Copy className="h-4 w-4 text-foreground-muted" />
          )}
        </button>
      </div>

      {/* Code Content */}
      <div className="flex-1 min-h-0 min-w-0 overflow-hidden">
        <MonacoEditor
          value={content}
          language={language}
          theme={effectiveTheme}
          beforeMount={handleBeforeMount}
          options={{
            readOnly: true,
            minimap: { enabled: false },
            scrollBeyondLastLine: false,
            fontSize: 13,
            lineNumbers: "on",
            automaticLayout: true,
            wordWrap: "on",
            semanticHighlighting: { enabled: false },
          }}
        />
      </div>
    </div>
  );
}
