"use client";

import { useProjectStore } from "@/lib/store";
import { Highlight, themes } from "prism-react-renderer";
import { Copy, Check } from "lucide-react";
import { useState } from "react";

export function CodeViewer() {
  const { selectedFile, fileContent, fileLanguage, generatedFiles } =
    useProjectStore();
  const [copied, setCopied] = useState(false);

  // Try to get content from generated files if not loaded
  const content =
    fileContent ||
    generatedFiles.find((f) => f.file_path === selectedFile)?.file_content ||
    null;

  const language = fileLanguage || "text";

  const handleCopy = async () => {
    if (content) {
      await navigator.clipboard.writeText(content);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
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
    <div className="flex-1 flex flex-col overflow-hidden">
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
      <div className="flex-1 overflow-auto">
        <Highlight
          theme={themes.nightOwl}
          code={content}
          language={language as any}
        >
          {({ className, style, tokens, getLineProps, getTokenProps }) => (
            <pre
              className={`${className} p-4 text-sm font-mono leading-relaxed`}
              style={{ ...style, background: "transparent" }}
            >
              {tokens.map((line, i) => (
                <div key={i} {...getLineProps({ line })} className="table-row">
                  <span className="table-cell pr-4 text-foreground-subtle select-none text-right w-10">
                    {i + 1}
                  </span>
                  <span className="table-cell">
                    {line.map((token, key) => (
                      <span key={key} {...getTokenProps({ token })} />
                    ))}
                  </span>
                </div>
              ))}
            </pre>
          )}
        </Highlight>
      </div>
    </div>
  );
}
