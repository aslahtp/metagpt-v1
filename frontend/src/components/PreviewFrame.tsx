"use client";

import { useState } from "react";
import {
  ExternalLink,
  RefreshCw,
  Play,
  AlertCircle,
  Terminal,
} from "lucide-react";

interface PreviewFrameProps {
  projectId: string;
}

export function PreviewFrame({ projectId }: PreviewFrameProps) {
  const [previewUrl, setPreviewUrl] = useState("http://localhost:5173");
  const [iframeKey, setIframeKey] = useState(0);
  const [isLoading, setIsLoading] = useState(false);
  const [showInstructions, setShowInstructions] = useState(true);

  const handleRefresh = () => {
    setIframeKey((k) => k + 1);
    setIsLoading(true);
  };

  const handleLoad = () => {
    setIsLoading(false);
    setShowInstructions(false);
  };

  const handleOpenExternal = () => {
    window.open(previewUrl, "_blank");
  };

  const handleStartPreview = () => {
    setShowInstructions(false);
    setIsLoading(true);
    setIframeKey((k) => k + 1);
  };

  return (
    <div className="h-full flex flex-col bg-background">
      {/* Toolbar */}
      <div className="h-10 border-b border-border flex items-center px-3 gap-2 shrink-0 bg-background-secondary">
        <input
          type="text"
          value={previewUrl}
          onChange={(e) => setPreviewUrl(e.target.value)}
          placeholder="http://localhost:5173"
          className="flex-1 px-2 py-1 text-xs rounded border border-border bg-background focus:outline-none focus:ring-1 focus:ring-accent font-mono"
        />
        <button
          onClick={handleStartPreview}
          className="flex items-center gap-1 px-2 py-1 text-xs rounded bg-accent text-white hover:bg-accent-hover transition-colors"
        >
          <Play className="h-3 w-3" />
          Load
        </button>
        <button
          onClick={handleRefresh}
          className="p-1.5 rounded hover:bg-background-tertiary transition-colors"
          title="Refresh"
        >
          <RefreshCw
            className={`h-4 w-4 text-foreground-muted ${
              isLoading ? "animate-spin" : ""
            }`}
          />
        </button>
        <button
          onClick={handleOpenExternal}
          className="p-1.5 rounded hover:bg-background-tertiary transition-colors"
          title="Open in new tab"
        >
          <ExternalLink className="h-4 w-4 text-foreground-muted" />
        </button>
      </div>

      {/* Preview Area */}
      <div className="flex-1 relative bg-white">
        {showInstructions ? (
          <div className="absolute inset-0 flex items-center justify-center bg-background-tertiary">
            <div className="max-w-md text-center p-8">
              <div className="w-16 h-16 rounded-xl bg-accent/10 flex items-center justify-center mx-auto mb-4">
                <Terminal className="h-8 w-8 text-accent" />
              </div>
              <h3 className="text-lg font-medium mb-2">Start the Dev Server</h3>
              <p className="text-sm text-foreground-muted mb-6">
                Run the generated project to see the live preview:
              </p>
              <div className="text-left bg-background-secondary p-4 rounded-lg space-y-2 font-mono text-sm">
                <div className="flex items-center gap-2">
                  <span className="text-foreground-subtle">$</span>
                  <code className="text-accent">
                    cd backend/projects/{projectId}/files
                  </code>
                </div>
                <div className="flex items-center gap-2">
                  <span className="text-foreground-subtle">$</span>
                  <code className="text-accent">npm install</code>
                </div>
                <div className="flex items-center gap-2">
                  <span className="text-foreground-subtle">$</span>
                  <code className="text-accent">npm run dev</code>
                </div>
              </div>
              <p className="text-xs text-foreground-subtle mt-4 mb-4">
                Once the dev server is running, click Load to preview
              </p>
              <button onClick={handleStartPreview} className="btn-primary">
                Load Preview
              </button>
            </div>
          </div>
        ) : (
          <>
            {isLoading && (
              <div className="absolute inset-0 flex items-center justify-center bg-background-tertiary/80 z-10">
                <div className="flex items-center gap-3">
                  <div className="h-5 w-5 border-2 border-accent/30 border-t-accent rounded-full animate-spin" />
                  <span className="text-foreground-muted">
                    Loading preview...
                  </span>
                </div>
              </div>
            )}
            <iframe
              key={iframeKey}
              src={previewUrl}
              className="w-full h-full border-0"
              title="Project Preview"
              onLoad={handleLoad}
              onError={() => setIsLoading(false)}
              sandbox="allow-scripts allow-same-origin allow-forms allow-popups allow-modals"
            />
          </>
        )}
      </div>
    </div>
  );
}
