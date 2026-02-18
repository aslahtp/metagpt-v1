"use client";

import { useState, useRef, useEffect, useCallback } from "react";
import { useProjectStore } from "@/lib/store";
import { createSandbox, killSandbox } from "@/lib/api";
import {
  ExternalLink,
  RefreshCw,
  Play,
  Cloud,
  Monitor,
  Tablet,
  Smartphone,
  Maximize,
  XCircle,
  AlertCircle,
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
  const [sandboxError, setSandboxError] = useState<string | null>(null);
  const [device, setDevice] = useState<DevicePreset>("responsive");
  const {
    previewInitialized,
    setPreviewInitialized,
    sandboxUrl,
    setSandboxUrl,
    sandboxId,
    setSandboxId,
    sandboxLoading,
    setSandboxLoading,
  } = useProjectStore();

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

  // Cleanup sandbox on unmount
  useEffect(() => {
    return () => {
      if (sandboxId) {
        killSandbox(projectId).catch(() => {});
      }
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [sandboxId]);

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

  // Load preview using manual URL (localhost)
  const handleLoadManual = () => {
    setSandboxError(null);
    setPreviewInitialized(true);
    setIsLoading(true);
    setIframeKey((k) => k + 1);
  };

  // Launch cloud preview via E2B sandbox
  const handleLaunchSandbox = async () => {
    setSandboxError(null);
    setSandboxLoading(true);
    setIsLoading(true);

    try {
      const info = await createSandbox(projectId);
      if (info.preview_url) {
        setSandboxUrl(info.preview_url);
        setSandboxId(info.sandbox_id);
        setPreviewUrl(info.preview_url);
        setPreviewInitialized(true);
        setIframeKey((k) => k + 1);
      }
    } catch (err) {
      const msg = err instanceof Error ? err.message : "Failed to create sandbox";
      setSandboxError(msg);
      setIsLoading(false);
    } finally {
      setSandboxLoading(false);
    }
  };

  // Kill sandbox
  const handleKillSandbox = async () => {
    try {
      await killSandbox(projectId);
    } catch {
      // ignore
    }
    setSandboxUrl(null);
    setSandboxId(null);
    setPreviewInitialized(false);
    setIsLoading(false);
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
          onClick={handleLoadManual}
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
        {sandboxId && (
          <button
            onClick={handleKillSandbox}
            className="flex items-center gap-1 px-2 py-1 text-xs rounded bg-red-500/10 text-red-400 hover:bg-red-500/20 transition-colors"
            title="Stop cloud sandbox"
          >
            <XCircle className="h-3 w-3" />
            Stop
          </button>
        )}
      </div>

      {/* Preview Area */}
      <div ref={containerRef} className="flex-1 relative bg-white overflow-hidden">
        {!previewInitialized ? (
          <div className="absolute inset-0 flex items-center justify-center bg-background-tertiary">
            <div className="max-w-md text-center p-8">
              <div className="w-16 h-16 rounded-xl bg-accent/10 flex items-center justify-center mx-auto mb-4">
                <Cloud className="h-8 w-8 text-accent" />
              </div>
              <h3 className="text-lg font-medium mb-2">Preview Project</h3>
              <p className="text-sm text-foreground-muted mb-6">
                Launch a cloud sandbox to preview the generated project, or load a
                local dev server URL.
              </p>

              {/* Sandbox error */}
              {sandboxError && (
                <div className="flex items-start gap-2 text-left bg-red-500/10 border border-red-500/20 p-3 rounded-lg mb-4">
                  <AlertCircle className="h-4 w-4 text-red-400 shrink-0 mt-0.5" />
                  <p className="text-xs text-red-400">{sandboxError}</p>
                </div>
              )}

              {/* Cloud preview button */}
              <button
                onClick={handleLaunchSandbox}
                disabled={sandboxLoading}
                className="btn-primary w-full flex items-center justify-center gap-2 mb-3"
              >
                {sandboxLoading ? (
                  <>
                    <div className="h-4 w-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                    Creating sandbox...
                  </>
                ) : (
                  <>
                    <Cloud className="h-4 w-4" />
                    Launch Cloud Preview
                  </>
                )}
              </button>

              {/* Divider */}
              <div className="flex items-center gap-3 mb-3">
                <div className="flex-1 h-px bg-border" />
                <span className="text-xs text-foreground-subtle">or</span>
                <div className="flex-1 h-px bg-border" />
              </div>

              {/* Local preview option */}
              <button
                onClick={handleLoadManual}
                className="btn-ghost w-full text-sm flex items-center justify-center gap-2"
              >
                <Play className="h-4 w-4" />
                Load from localhost
              </button>

              <p className="text-xs text-foreground-subtle mt-4">
                Cloud preview powered by{" "}
                <a
                  href="https://e2b.dev"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-accent hover:underline"
                >
                  E2B
                </a>
              </p>
            </div>
          </div>
        ) : (
          <>
            {isLoading && (
              <div className="absolute inset-0 flex items-center justify-center bg-background-tertiary/80 z-10">
                <div className="flex flex-col items-center gap-3">
                  <div className="h-5 w-5 border-2 border-accent/30 border-t-accent rounded-full animate-spin" />
                  <span className="text-foreground-muted">
                    {sandboxLoading
                      ? "Setting up sandbox (this may take a minute)..."
                      : "Loading preview..."}
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
