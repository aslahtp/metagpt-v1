"use client";

import { useEffect, useState, useCallback, useRef } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import {
  Code,
  Monitor,
  Download,
  Settings,
  Check,
  Palette,
  FolderX,
  ChevronRight,
  ChevronLeft,
  RefreshCw,
  PanelLeft,
  PanelRight,
  Sun,
  Moon,
} from "lucide-react";
import { MaterialIconWithFallback } from "@/components/MaterialIconWithFallback";
import {
  getProject,
  runPipeline,
  getFileTree,
  getFileContent,
  downloadProjectZip,
} from "@/lib/api";
import { useProjectStore } from "@/lib/store";
import { useAuthStore } from "@/lib/authStore";
import { EDITOR_THEMES } from "@/lib/editorThemes";
import { ExecutionTimeline } from "@/components/ExecutionTimeline";
import { FileExplorer } from "@/components/FileExplorer";
import { CodeViewer } from "@/components/CodeViewer";
import { ChatPanel } from "@/components/ChatPanel";
import { AgentOutputs } from "@/components/AgentOutputs";
import { PreviewFrame } from "@/components/PreviewFrame";

export default function ProjectPage() {
  const params = useParams();
  const projectId = params.id as string;
  const router = useRouter();
  const { token, initialize } = useAuthStore();

  useEffect(() => {
    initialize();
  }, [initialize]);

  useEffect(() => {
    if (!token) {
      router.replace("/signin");
    }
  }, [token, router]);

  const {
    project,
    setProject,
    pipelineRunning,
    setPipelineRunning,
    setCurrentAgent,
    setProgress,
    setFileTree,
    selectedFile,
    setSelectedFile,
    setFileContent,
    setFileLanguage,
    setGeneratedFiles,
    reset,
  } = useProjectStore();

  const {
    editorTheme,
    setEditorTheme,
    hideNodeModules,
    setHideNodeModules,
    uiTheme,
    setUiTheme,
  } = useProjectStore();

  const [rightPanelTab, setRightPanelTab] = useState<
    "timeline" | "outputs" | "chat"
  >(
    "timeline"
  );
  const [centerView, setCenterView] = useState<"code" | "preview">("code");
  const [error, setError] = useState<string | null>(null);
  const [downloading, setDownloading] = useState(false);
  const [refreshingFiles, setRefreshingFiles] = useState(false);
  const [showFileExplorer, setShowFileExplorer] = useState(true);
  const [showRightPanel, setShowRightPanel] = useState(true);
  const [settingsOpen, setSettingsOpen] = useState(false);
  const [settingsView, setSettingsView] = useState<"main" | "themes">("main");
  const settingsRef = useRef<HTMLDivElement>(null);

  // Close settings dropdown on click outside
  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (
        settingsRef.current &&
        !settingsRef.current.contains(event.target as Node)
      ) {
        setSettingsOpen(false);
        setSettingsView("main");
      }
    }
    if (settingsOpen) {
      document.addEventListener("mousedown", handleClickOutside);
      return () =>
        document.removeEventListener("mousedown", handleClickOutside);
    }
  }, [settingsOpen]);

  // Fetch project data
  const fetchProject = useCallback(async () => {
    try {
      const projectData = await getProject(projectId);
      setProject(projectData);

      // If completed, load file tree
      if (projectData.state.pipeline_status?.stage === "completed") {
        try {
          const tree = await getFileTree(projectId);
          setFileTree(tree.root);
        } catch {
          // No files yet
        }
      }

      // Set generated files if available
      if (projectData.state.engineer_output?.files) {
        setGeneratedFiles(projectData.state.engineer_output.files);
      }

      // Update progress
      setProgress(projectData.state.pipeline_status?.progress || 0);
      setCurrentAgent(projectData.state.pipeline_status?.current_agent || null);

      return projectData;
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : "";
      if (message === "UNAUTHORIZED") {
        router.replace("/signin");
        return null;
      }
      setError("Failed to load project");
      return null;
    }
  }, [
    projectId,
    setProject,
    setFileTree,
    setGeneratedFiles,
    setProgress,
    setCurrentAgent,
    router,
  ]);

  // Run pipeline with fire-and-forget + polling for real-time progress
  const handleRunPipeline = async () => {
    if (pipelineRunning) return;

    setPipelineRunning(true);
    setError(null);
    setCurrentAgent("manager");
    setProgress(0);

    // Fire the pipeline in the background (don't await — it blocks until done)
    runPipeline(projectId).catch((err) => {
      console.error("Pipeline run error:", err);
    });

    // Poll for status updates — the backend persists state after each agent
    const poll = async () => {
      try {
        const projectData = await getProject(projectId);
        setProject(projectData);

        const status = projectData.state.pipeline_status;
        if (status) {
          setProgress(status.progress);
          setCurrentAgent(status.current_agent);
        }

        if (status?.stage === "completed") {
          setPipelineRunning(false);

          // Load file tree
          try {
            const tree = await getFileTree(projectId);
            setFileTree(tree.root);
          } catch {
            // Files may not exist yet
          }

          // Set generated files
          if (projectData.state.engineer_output?.files) {
            setGeneratedFiles(projectData.state.engineer_output.files);
          }
          return; // Stop polling
        }

        if (status?.stage === "error") {
          setPipelineRunning(false);
          setError(status.message || "Pipeline execution failed");
          return; // Stop polling
        }

        // Continue polling
        setTimeout(poll, 1500);
      } catch {
        // Retry on transient errors
        setTimeout(poll, 2000);
      }
    };

    // Start polling after a brief delay to let the backend initialize
    setTimeout(poll, 500);
  };

  // Fetch file content
  const handleSelectFile = async (path: string) => {
    setSelectedFile(path);
    setCenterView("code"); // Switch to code view when selecting a file

    try {
      const file = await getFileContent(projectId, path);
      setFileContent(file.content);
      setFileLanguage(file.language);
    } catch {
      setFileContent("// Failed to load file content");
      setFileLanguage("text");
    }
  };

  // Refresh file tree
  const handleRefreshFiles = async () => {
    if (refreshingFiles) return;
    setRefreshingFiles(true);
    try {
      const tree = await getFileTree(projectId);
      setFileTree(tree.root);
    } catch {
      // Silently fail — tree may not exist yet
    } finally {
      setRefreshingFiles(false);
    }
  };

  // Called by ChatPanel after files are modified/created via chat
  const handleChatFilesModified = async (files: string[]) => {
    // Refresh file tree so new files appear in the explorer
    try {
      const tree = await getFileTree(projectId);
      setFileTree(tree.root);
    } catch {}

    // If the currently open file was modified, re-fetch its content
    if (selectedFile && files.includes(selectedFile)) {
      try {
        const file = await getFileContent(projectId, selectedFile);
        setFileContent(file.content);
        setFileLanguage(file.language);
      } catch {}
    }
  };

  // Download project as zip
  const handleDownloadZip = async () => {
    if (downloading) return;
    setDownloading(true);
    try {
      await downloadProjectZip(projectId);
    } catch {
      setError("Failed to download project files");
    } finally {
      setDownloading(false);
    }
  };

  // Reset store when navigating to a new project
  useEffect(() => {
    reset();
  }, [projectId]);

  // Initial load
  useEffect(() => {
    fetchProject().then((p) => {
      // Auto-run pipeline if pending
      if (p?.state.pipeline_status?.stage === "pending") {
        handleRunPipeline();
      }
    });
  }, [fetchProject]);

  if (!project) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="flex items-center gap-3">
          <div className="h-5 w-5 border-2 border-accent/30 border-t-accent rounded-full animate-spin" />
          <span className="text-foreground-muted">Loading project...</span>
        </div>
      </div>
    );
  }

  const isReactProject = project.preview?.preview_supported;

  return (
    <div className="h-screen flex flex-col">
      {/* Header */}
      <header className="h-14 border-b border-border flex items-center px-4 gap-4 shrink-0">
        <Link href="/" className="flex items-center hover:opacity-80 transition-opacity duration-200">
          <span className="font-medium">MetaGPT</span>
        </Link>
        <div className="h-4 w-px bg-border" />
        <div className="flex-1 min-w-0" title={project.prompt}>
          <h1 className="text-sm font-medium truncate">
            {project.name || "New Project"}
          </h1>
          <p className="text-xs text-foreground-muted truncate">
            {project.prompt.slice(0, 60)}...
          </p>
        </div>
        <div className="flex items-center gap-2">
          {/* UI theme toggle (light/dark) */}
          <button
            onClick={() => setUiTheme(uiTheme === "dark" ? "light" : "dark")}
            className="flex items-center p-1 rounded-md text-foreground-muted hover:text-foreground hover:bg-background-tertiary transition-colors"
            title={uiTheme === "dark" ? "Switch to light mode" : "Switch to dark mode"}
          >
            {uiTheme === "dark" ? (
              <Moon className="h-4 w-4" />
            ) : (
              <Sun className="h-4 w-4" />
            )}
          </button>
          <div className="flex items-center">
            <button
              onClick={() => setShowFileExplorer(!showFileExplorer)}
              className={`flex items-center p-0.5 rounded transition-colors ${
                showFileExplorer
                  ? "text-foreground-muted hover:text-foreground hover:bg-background-tertiary"
                  : "text-accent bg-accent/10"
              }`}
              title={showFileExplorer ? "Hide file explorer" : "Show file explorer"}
            >
              <MaterialIconWithFallback
                name="dock_to_right"
                fallback={PanelLeft}
                fillFallback={true}
              />
            </button>
            <button
              onClick={() => setShowRightPanel(!showRightPanel)}
              className={`flex items-center p-0.5 rounded transition-colors ${
                showRightPanel
                  ? "text-foreground-muted hover:text-foreground hover:bg-background-tertiary"
                  : "text-accent bg-accent/10"
              }`}
              title={showRightPanel ? "Hide right panel" : "Show right panel"}
            >
              <MaterialIconWithFallback
                name="dock_to_left"
                fallback={PanelRight}
                fillFallback={true}
              />
            </button>
          </div>
          <div className="h-4 w-px bg-border" />
          {pipelineRunning && (
            <div className="flex items-center gap-2 text-sm text-foreground-muted">
              <div className="h-4 w-4 border-2 border-accent/30 border-t-accent rounded-full animate-spin" />
              <span>Generating...</span>
            </div>
          )}
          {project.state.pipeline_status?.stage === "completed" && (
            <span className="text-sm text-success">Complete</span>
          )}
        </div>
      </header>

      {/* Main Content */}
      <div className="flex-1 flex overflow-hidden">
        {/* Left Panel - File Explorer */}
        {showFileExplorer && (
        <div className="w-64 border-r border-border flex flex-col shrink-0">
          <div className="p-3 border-b border-border flex items-center justify-between">
            <h2 className="text-sm font-medium">Files</h2>
            <div className="flex items-center gap-1">
              {/* Refresh file tree */}
              <button
                onClick={handleRefreshFiles}
                disabled={refreshingFiles}
                title="Refresh file list"
                className="p-1.5 rounded text-foreground-muted hover:text-accent hover:bg-accent/10 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              >
                <RefreshCw
                  className={`h-3.5 w-3.5 ${refreshingFiles ? "animate-spin" : ""}`}
                />
              </button>

              {project.state.pipeline_status?.stage === "completed" && (
                <button
                  onClick={handleDownloadZip}
                  disabled={downloading}
                  title="Download as ZIP"
                  className="flex items-center gap-1.5 px-2 py-1 rounded text-xs font-medium text-foreground-muted hover:text-accent hover:bg-accent/10 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {downloading ? (
                    <div className="h-3.5 w-3.5 border-2 border-accent/30 border-t-accent rounded-full animate-spin" />
                  ) : (
                    <Download className="h-3.5 w-3.5" />
                  )}
                  <span>{downloading ? "Zipping..." : "ZIP"}</span>
                </button>
              )}

              {/* Settings Button */}
              <div className="relative" ref={settingsRef}>
                <button
                  onClick={() => {
                    setSettingsOpen(!settingsOpen);
                    if (settingsOpen) setSettingsView("main");
                  }}
                  className={`p-1.5 rounded transition-colors ${
                    settingsOpen
                      ? "bg-accent/10 text-accent"
                      : "text-foreground-muted hover:text-foreground hover:bg-background-tertiary"
                  }`}
                  title="Settings"
                >
                  <Settings className="h-3.5 w-3.5" />
                </button>

                {/* Settings Dropdown */}
                {settingsOpen && (
                  <div className="absolute right-0 top-full mt-1 w-60 z-50 rounded-xl border border-border bg-background-secondary shadow-2xl shadow-black/40 overflow-hidden animate-in">
                    {settingsView === "main" ? (
                      /* ── Main Settings View ── */
                      <div className="px-1.5 py-1.5 space-y-0.5">
                        {/* Hide node_modules */}
                        <button
                          onClick={() => setHideNodeModules(!hideNodeModules)}
                          className="w-full flex items-center justify-between gap-2 px-2.5 py-2.5 rounded-lg text-left transition-all duration-150 hover:bg-background-tertiary group"
                        >
                          <div className="flex items-center gap-2.5">
                            <FolderX className="h-3.5 w-3.5 text-foreground-subtle group-hover:text-foreground-muted shrink-0" />
                            <span className="text-xs font-medium text-foreground-muted group-hover:text-foreground">
                              Hide node_modules
                            </span>
                          </div>
                          <div
                            className={`relative w-8 h-[18px] rounded-full transition-colors duration-200 shrink-0 ${
                              hideNodeModules
                                ? "bg-accent"
                                : "bg-foreground-subtle/30"
                            }`}
                          >
                            <div
                              className={`absolute top-[2px] h-[14px] w-[14px] rounded-full shadow-sm transition-all duration-200 border ${
                                hideNodeModules
                                  ? "translate-x-[16px] bg-background-secondary border-white/20"
                                  : "translate-x-[2px] bg-background-secondary border-foreground-subtle/30"
                              }`}
                            />
                          </div>
                        </button>

                        {/* Editor Theme → opens sub-panel */}
                        <button
                          onClick={() => setSettingsView("themes")}
                          className="w-full flex items-center justify-between gap-2 px-2.5 py-2.5 rounded-lg text-left transition-all duration-150 hover:bg-background-tertiary group"
                        >
                          <div className="flex items-center gap-2.5">
                            <Palette className="h-3.5 w-3.5 text-foreground-subtle group-hover:text-foreground-muted shrink-0" />
                            <span className="text-xs font-medium text-foreground-muted group-hover:text-foreground">
                              Editor Theme
                            </span>
                          </div>
                          <div className="flex items-center gap-1.5">
                            <span className="text-[10px] text-foreground-subtle truncate max-w-[72px]">
                              {EDITOR_THEMES.find((t) => t.id === editorTheme)?.label ?? "Default"}
                            </span>
                            <ChevronRight className="h-3.5 w-3.5 text-foreground-subtle shrink-0" />
                          </div>
                        </button>
                      </div>
                    ) : (
                      /* ── Theme Picker Sub-panel ── */
                      <div>
                        {/* Back header */}
                        <button
                          onClick={() => setSettingsView("main")}
                          className="w-full flex items-center gap-2 px-3 py-2.5 border-b border-border text-left hover:bg-background-tertiary transition-colors"
                        >
                          <ChevronLeft className="h-3.5 w-3.5 text-foreground-subtle" />
                          <span className="text-xs font-medium text-foreground-muted">
                            Editor Theme
                          </span>
                        </button>

                        {/* Theme list */}
                        <div className="px-1.5 py-1.5 max-h-72 overflow-y-auto space-y-0.5">
                          {EDITOR_THEMES.map((theme) => (
                            <button
                              key={theme.id}
                              onClick={() => setEditorTheme(theme.id)}
                              className={`w-full flex items-center gap-2.5 px-2.5 py-[7px] rounded-lg text-left transition-all duration-150 group ${
                                editorTheme === theme.id
                                  ? "bg-accent/10"
                                  : "hover:bg-background-tertiary"
                              }`}
                            >
                              {/* Color Swatch */}
                              <div
                                className="w-5 h-5 rounded-md shrink-0 border border-white/10 flex items-center justify-center overflow-hidden"
                                style={{ backgroundColor: theme.swatch[0] }}
                              >
                                <div className="flex flex-col items-center gap-px">
                                  <div
                                    className="w-2.5 h-[2px] rounded-full"
                                    style={{ backgroundColor: theme.swatch[2] }}
                                  />
                                  <div
                                    className="w-2 h-[2px] rounded-full opacity-60"
                                    style={{ backgroundColor: theme.swatch[1] }}
                                  />
                                </div>
                              </div>

                              {/* Label */}
                              <span
                                className={`text-xs font-medium flex-1 ${
                                  editorTheme === theme.id
                                    ? "text-accent"
                                    : "text-foreground-muted group-hover:text-foreground"
                                }`}
                              >
                                {theme.label}
                              </span>

                              {/* Check Mark */}
                              {editorTheme === theme.id && (
                                <Check className="h-3.5 w-3.5 text-accent shrink-0" />
                              )}
                            </button>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                )}
              </div>
            </div>
          </div>
          <div className="flex-1 overflow-auto scrollbar-auto-hide">
            <FileExplorer onSelectFile={handleSelectFile} />
          </div>
        </div>
        )}

        {/* Center Panel - Code Viewer / Preview */}
        <div className="flex-1 flex flex-col min-w-0">
          {/* Center Panel Tabs */}
          {isReactProject && (
            <div className="h-10 border-b border-border flex items-center px-2 gap-1 shrink-0">
              <button
                onClick={() => setCenterView("code")}
                className={`flex items-center gap-1.5 px-3 py-1.5 rounded text-sm font-medium transition-colors ${
                  centerView === "code"
                    ? "bg-accent/10 text-accent"
                    : "text-foreground-muted hover:text-foreground hover:bg-background-tertiary"
                }`}
              >
                <Code className="h-4 w-4" />
                Code
              </button>
              <button
                onClick={() => setCenterView("preview")}
                className={`flex items-center gap-1.5 px-3 py-1.5 rounded text-sm font-medium transition-colors ${
                  centerView === "preview"
                    ? "bg-accent/10 text-accent"
                    : "text-foreground-muted hover:text-foreground hover:bg-background-tertiary"
                }`}
              >
                <Monitor className="h-4 w-4" />
                Preview
              </button>
              {project.preview?.framework && (
                <span className="ml-auto text-xs px-2 py-0.5 rounded bg-success/10 text-success">
                  {project.preview.framework} detected
                </span>
              )}
            </div>
          )}

          {/* Center Content */}
          <div className="flex-1 flex flex-col min-h-0 min-w-0">
            <div
              className={
                centerView === "code"
                  ? "flex-1 min-h-0 min-w-0 flex"
                  : "hidden"
              }
            >
              <CodeViewer />
            </div>
            <div
              className={
                centerView === "preview"
                  ? "flex-1 min-h-0 min-w-0 flex"
                  : "hidden"
              }
            >
              <PreviewFrame projectId={projectId} />
            </div>
          </div>
        </div>

        {/* Right Panel - Timeline/Outputs */}
        {showRightPanel && (
        <div className="w-80 border-l border-border flex flex-col shrink-0">
          {/* Tabs */}
          <div className="flex border-b border-border shrink-0">
            <button
              onClick={() => setRightPanelTab("timeline")}
              className={`flex-1 px-3 py-2 text-sm font-medium ${
                rightPanelTab === "timeline"
                  ? "text-accent border-b-2 border-accent"
                  : "text-foreground-muted hover:text-foreground"
              }`}
            >
              Timeline
            </button>
            <button
              onClick={() => setRightPanelTab("outputs")}
              className={`flex-1 px-3 py-2 text-sm font-medium ${
                rightPanelTab === "outputs"
                  ? "text-accent border-b-2 border-accent"
                  : "text-foreground-muted hover:text-foreground"
              }`}
            >
              Outputs
            </button>
            <button
              onClick={() => setRightPanelTab("chat")}
              className={`flex-1 px-3 py-2 text-sm font-medium ${
                rightPanelTab === "chat"
                  ? "text-accent border-b-2 border-accent"
                  : "text-foreground-muted hover:text-foreground"
              }`}
            >
              Chat
            </button>
          </div>

          {/* Tab Content */}
          <div className="flex-1 min-h-0 overflow-auto flex flex-col">
            {rightPanelTab === "timeline" && <ExecutionTimeline />}
            {rightPanelTab === "outputs" && <AgentOutputs />}
            {rightPanelTab === "chat" && (
              <ChatPanel projectId={projectId} embedded onFilesModified={handleChatFilesModified} />
            )}
          </div>
        </div>
        )}
      </div>

      {/* Error Toast */}
      {error && (
        <div className="fixed bottom-20 right-4 bg-error text-white px-4 py-2 rounded-lg shadow-lg">
          {error}
          <button
            onClick={() => setError(null)}
            className="ml-2 text-white/80 hover:text-white"
          >
            ×
          </button>
        </div>
      )}
    </div>
  );
}
