"use client";

import { useState } from "react";
import { useProjectStore } from "@/lib/store";
import {
  ExternalLink,
  RefreshCw,
  Monitor,
  Play,
  AlertCircle,
} from "lucide-react";

export function PreviewPanel() {
  const { project, previewEnabled, setPreviewEnabled } = useProjectStore();
  const [previewUrl, setPreviewUrl] = useState("http://localhost:5173");
  const [iframeKey, setIframeKey] = useState(0);
  const [iframeError, setIframeError] = useState(false);

  if (!project?.preview?.preview_supported) {
    return (
      <div className="p-4 text-center text-foreground-muted">
        <Monitor className="h-12 w-12 mx-auto mb-3 text-foreground-subtle" />
        <p className="text-sm">Preview not available</p>
        <p className="text-xs text-foreground-subtle mt-1">
          Preview is only available for React/Next.js projects.
        </p>
      </div>
    );
  }

  const { is_react_project, is_nextjs_project, framework, entry_file } =
    project.preview;

  const handleRefresh = () => {
    setIframeKey((k) => k + 1);
    setIframeError(false);
  };

  const handleOpenExternal = () => {
    window.open(previewUrl, "_blank");
  };

  return (
    <div className="flex flex-col h-full">
      {/* Preview Header */}
      <div className="p-3 border-b border-border flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Monitor className="h-4 w-4 text-accent" />
          <span className="text-sm font-medium">Preview</span>
          {framework && (
            <span className="text-xs px-1.5 py-0.5 rounded bg-accent/10 text-accent">
              {framework}
            </span>
          )}
        </div>
        <div className="flex items-center gap-1">
          <button
            onClick={() => setPreviewEnabled(!previewEnabled)}
            className="btn-ghost text-xs"
          >
            {previewEnabled ? "Hide" : "Show"}
          </button>
          <button
            onClick={handleRefresh}
            className="p-1.5 rounded hover:bg-background-tertiary"
            title="Refresh preview"
          >
            <RefreshCw className="h-4 w-4 text-foreground-muted" />
          </button>
          <button
            onClick={handleOpenExternal}
            className="p-1.5 rounded hover:bg-background-tertiary"
            title="Open in new tab"
          >
            <ExternalLink className="h-4 w-4 text-foreground-muted" />
          </button>
        </div>
      </div>

      {/* URL Input */}
      {previewEnabled && (
        <div className="p-2 border-b border-border flex items-center gap-2">
          <input
            type="text"
            value={previewUrl}
            onChange={(e) => setPreviewUrl(e.target.value)}
            placeholder="http://localhost:5173"
            className="flex-1 px-2 py-1 text-xs rounded border border-border bg-background-secondary focus:outline-none focus:ring-1 focus:ring-accent"
          />
          <button
            onClick={handleRefresh}
            className="btn-primary text-xs py-1 px-2 flex items-center gap-1"
          >
            <Play className="h-3 w-3" />
            Load
          </button>
        </div>
      )}

      {/* Preview Content */}
      <div className="flex-1 bg-background-tertiary relative">
        {previewEnabled ? (
          <>
            {iframeError ? (
              <div className="h-full flex items-center justify-center">
                <div className="text-center p-6 max-w-sm">
                  <AlertCircle className="h-12 w-12 mx-auto mb-3 text-warning" />
                  <h3 className="font-medium mb-2">Cannot load preview</h3>
                  <p className="text-sm text-foreground-muted mb-4">
                    Make sure the dev server is running:
                  </p>
                  <div className="text-left bg-background-secondary p-3 rounded-lg space-y-1">
                    <code className="text-xs block font-mono text-accent">
                      cd projects/{project.id}/files
                    </code>
                    <code className="text-xs block font-mono text-accent">
                      npm install
                    </code>
                    <code className="text-xs block font-mono text-accent">
                      npm run dev
                    </code>
                  </div>
                  <button
                    onClick={handleRefresh}
                    className="btn-primary mt-4 text-sm"
                  >
                    Try Again
                  </button>
                </div>
              </div>
            ) : (
              <iframe
                key={iframeKey}
                src={previewUrl}
                className="w-full h-full border-0"
                title="Project Preview"
                onError={() => setIframeError(true)}
                sandbox="allow-scripts allow-same-origin allow-forms allow-popups"
              />
            )}
          </>
        ) : (
          <div className="h-full flex items-center justify-center">
            <div className="text-center p-6">
              <Monitor className="h-12 w-12 mx-auto mb-3 text-foreground-subtle" />
              <p className="text-sm text-foreground-muted mb-2">
                Preview is hidden
              </p>
              <p className="text-xs text-foreground-subtle mb-4">
                First, run the generated project:
              </p>
              <div className="text-left bg-background-secondary p-3 rounded-lg space-y-1 mb-4">
                <code className="text-xs block font-mono text-accent">
                  cd projects/{project.id}/files
                </code>
                <code className="text-xs block font-mono text-accent">
                  npm install && npm run dev
                </code>
              </div>
              <button
                onClick={() => setPreviewEnabled(true)}
                className="btn-primary text-sm"
              >
                Show Preview
              </button>
            </div>
          </div>
        )}
      </div>

      {/* Project Info */}
      <div className="p-3 border-t border-border text-xs text-foreground-muted">
        <div className="flex items-center justify-between">
          <span>
            {is_nextjs_project
              ? "Next.js"
              : is_react_project
              ? "React"
              : "Unknown"}{" "}
            Project
          </span>
          <span>{project.state.engineer_output?.files.length || 0} files</span>
        </div>
      </div>
    </div>
  );
}
