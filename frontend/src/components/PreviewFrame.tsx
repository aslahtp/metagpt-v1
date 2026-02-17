"use client";

import { useState, useRef, useEffect, useCallback } from "react";
import { useProjectStore } from "@/lib/store";
import {
  ExternalLink,
  RefreshCw,
  Play,
  Terminal,
  Monitor,
  Tablet,
  Smartphone,
  Maximize,
} from "lucide-react";

interface PreviewFrameProps {
  projectId: string;
}

type DevicePreset = "responsive" | "mobile" | "desktop" | "tablet";

const DEVICE_WIDTHS: Record<DevicePreset, number | null> = {
  responsive: null, // fits container width, no scaling
  mobile: 375,
  desktop: 1440,
  tablet: 768,
};

const DEVICE_ICONS: Record<DevicePreset, React.ComponentType<{ className?: string }>> = {
  responsive: Maximize,
  mobile: Smartphone,
  tablet: Tablet,
  desktop: Monitor,
};

const DEVICE_LABELS: Record<DevicePreset, string> = {
  responsive: "Responsive",
  mobile: "Mobile",
  tablet: "Tablet",
  desktop: "Desktop",
};

export function PreviewFrame({ projectId }: PreviewFrameProps) {
  const [previewUrl, setPreviewUrl] = useState("http://localhost:5173");
  const [iframeKey, setIframeKey] = useState(0);
  const [isLoading, setIsLoading] = useState(false);
  const [device, setDevice] = useState<DevicePreset>("responsive");
  const { previewInitialized, setPreviewInitialized } = useProjectStore();

  const containerRef = useRef<HTMLDivElement>(null);
  const [containerSize, setContainerSize] = useState({ width: 0, height: 0 });
  const [layoutMenuOpen, setLayoutMenuOpen] = useState(false);
  const layoutMenuRef = useRef<HTMLDivElement>(null);

  // Close layout menu when clicking outside
  useEffect(() => {
    if (!layoutMenuOpen) return;
    const handleClickOutside = (e: MouseEvent) => {
      if (
        layoutMenuRef.current &&
        !layoutMenuRef.current.contains(e.target as Node)
      ) {
        setLayoutMenuOpen(false);
      }
    };
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, [layoutMenuOpen]);

  // Measure the container size using ResizeObserver
  useEffect(() => {
    const container = containerRef.current;
    if (!container) return;

    const observer = new ResizeObserver((entries) => {
      for (const entry of entries) {
        const { width, height } = entry.contentRect;
        setContainerSize({ width, height });
      }
    });

    observer.observe(container);
    return () => observer.disconnect();
  }, []);

  // Calculate iframe dimensions and scale
  const getIframeStyle = useCallback((): React.CSSProperties => {
    const targetWidth = DEVICE_WIDTHS[device];

    // "responsive" mode: iframe fills container naturally, no transform
    if (targetWidth === null || containerSize.width === 0) {
      return {
        width: "100%",
        height: "100%",
        border: "none",
      };
    }

    const containerW = containerSize.width;
    const containerH = containerSize.height;

    // If the container is wider than the target, center the iframe at natural size
    if (containerW >= targetWidth) {
      return {
        width: `${targetWidth}px`,
        height: "100%",
        border: "none",
        margin: "0 auto",
        display: "block",
      };
    }

    // Scale the iframe down to fit the container width
    const scale = containerW / targetWidth;
    const scaledHeight = containerH / scale;

    return {
      width: `${targetWidth}px`,
      height: `${scaledHeight}px`,
      border: "none",
      transform: `scale(${scale})`,
      transformOrigin: "top left",
    };
  }, [device, containerSize]);

  // Wrapper style to contain the scaled iframe
  const getWrapperStyle = useCallback((): React.CSSProperties => {
    const targetWidth = DEVICE_WIDTHS[device];

    if (targetWidth === null || containerSize.width === 0) {
      return { width: "100%", height: "100%" };
    }

    if (containerSize.width >= targetWidth) {
      return {
        width: "100%",
        height: "100%",
        display: "flex",
        justifyContent: "center",
      };
    }

    return {
      width: "100%",
      height: "100%",
      overflow: "hidden",
    };
  }, [device, containerSize]);

  const handleRefresh = () => {
    setIframeKey((k) => k + 1);
    setIsLoading(true);
  };

  const handleLoad = () => {
    setIsLoading(false);
    setPreviewInitialized(true);
  };

  const handleOpenExternal = () => {
    window.open(previewUrl, "_blank");
  };

  const handleStartPreview = () => {
    setPreviewInitialized(true);
    setIsLoading(true);
    setIframeKey((k) => k + 1);
  };

  return (
    <div className="h-full w-full flex flex-col bg-background">
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
          className="flex items-center gap-1 px-2 py-1 text-xs rounded bg-white text-black hover:bg-gray-200 transition-colors"
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
        <div className="relative" ref={layoutMenuRef}>
          <button
            onClick={() => setLayoutMenuOpen((o) => !o)}
            className="p-1.5 rounded hover:bg-background-tertiary transition-colors flex items-center"
            title={DEVICE_LABELS[device]}
          >
            {(() => {
              const Icon = DEVICE_ICONS[device];
              return <Icon className="h-4 w-4 text-foreground-muted" />;
            })()}
          </button>
          {layoutMenuOpen && (
            <div className="absolute top-full right-0 mt-1 py-1 min-w-[140px] rounded-md border border-border bg-background shadow-lg z-20">
              {(["responsive", "mobile", "tablet", "desktop"] as const).map(
                (preset) => {
                  const Icon = DEVICE_ICONS[preset];
                  return (
                    <button
                      key={preset}
                      onClick={() => {
                        setDevice(preset);
                        setLayoutMenuOpen(false);
                      }}
                      className={`w-full flex items-center gap-2 px-3 py-2 text-left text-sm transition-colors ${
                        device === preset
                          ? "bg-accent/15 text-accent"
                          : "text-foreground hover:bg-background-tertiary"
                      }`}
                      title={DEVICE_LABELS[preset]}
                    >
                      <Icon className="h-4 w-4 shrink-0" />
                      {DEVICE_LABELS[preset]}
                    </button>
                  );
                }
              )}
            </div>
          )}
        </div>
        <button
          onClick={handleOpenExternal}
          className="p-1.5 rounded hover:bg-background-tertiary transition-colors"
          title="Open in new tab"
        >
          <ExternalLink className="h-4 w-4 text-foreground-muted" />
        </button>
      </div>

      {/* Preview Area */}
      <div ref={containerRef} className="flex-1 relative bg-white overflow-hidden">
        {!previewInitialized ? (
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
            <div style={getWrapperStyle()}>
              <iframe
                key={iframeKey}
                src={previewUrl}
                style={getIframeStyle()}
                title="Project Preview"
                onLoad={handleLoad}
                onError={() => setIsLoading(false)}
                sandbox="allow-scripts allow-same-origin allow-forms allow-popups allow-modals"
              />
            </div>
          </>
        )}
      </div>
    </div>
  );
}
