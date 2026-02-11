"use client";

import { useEffect, useState, useCallback, useRef } from "react";
import { useParams } from "next/navigation";
import {
  Sparkles,
  Code,
  Monitor,
  Download,
  Settings,
  Check,
  Palette,
} from "lucide-react";
import {
  getProject,
  runPipeline,
  getFileTree,
  getFileContent,
  downloadProjectZip,
} from "@/lib/api";
import { useProjectStore } from "@/lib/store";
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
  } = useProjectStore();

  const { editorTheme, setEditorTheme } = useProjectStore();

  const [rightPanelTab, setRightPanelTab] = useState<"timeline" | "outputs">(
    "timeline"
  );
  const [centerView, setCenterView] = useState<"code" | "preview">("code");
  const [error, setError] = useState<string | null>(null);
  const [downloading, setDownloading] = useState(false);
  const [settingsOpen, setSettingsOpen] = useState(false);
  const settingsRef = useRef<HTMLDivElement>(null);

  // Close settings dropdown on click outside
  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (
        settingsRef.current &&
        !settingsRef.current.contains(event.target as Node)
      ) {
        setSettingsOpen(false);
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
    } catch (err) {
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
        <div className="flex items-center gap-2">
          <Sparkles className="h-5 w-5 text-accent" />
          <span className="font-medium">MetaGPT</span>
        </div>
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
        <div className="w-64 border-r border-border flex flex-col shrink-0">
          <div className="p-3 border-b border-border flex items-center justify-between">
            <h2 className="text-sm font-medium">Files</h2>
            <div className="flex items-center gap-1">
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
                  onClick={() => setSettingsOpen(!settingsOpen)}
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
                  <div className="absolute right-0 top-full mt-1 w-64 z-50 rounded-xl border border-border bg-background-secondary shadow-2xl shadow-black/40 overflow-hidden animate-in">
                    {/* Header */}
                    <div className="px-3 py-2.5 border-b border-border">
                      <div className="flex items-center gap-2">
                        <Settings className="h-3.5 w-3.5 text-foreground-subtle" />
                        <span className="text-xs font-semibold uppercase tracking-wider text-foreground-subtle">
                          Settings
                        </span>
                      </div>
                    </div>

                    {/* Editor Theme Section */}
                    <div className="p-2">
                      <div className="flex items-center gap-2 px-2 py-1.5 mb-1">
                        <Palette className="h-3.5 w-3.5 text-accent" />
                        <span className="text-xs font-medium text-foreground">
                          Editor Theme
                        </span>
                      </div>

                      <div className="max-h-72 overflow-y-auto space-y-0.5">
                        {EDITOR_THEMES.map((theme) => (
                          <button
                            key={theme.id}
                            onClick={() => {
                              setEditorTheme(theme.id);
                            }}
                            className={`w-full flex items-center gap-2.5 px-2 py-2 rounded-lg text-left transition-all duration-150 group ${
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
                  </div>
                )}
              </div>
            </div>
          </div>
          <div className="flex-1 overflow-auto">
            <FileExplorer onSelectFile={handleSelectFile} />
          </div>
        </div>

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
        <div className="w-80 border-l border-border flex flex-col shrink-0">
          {/* Tabs */}
          <div className="flex border-b border-border shrink-0">
            <button
              onClick={() => setRightPanelTab("timeline")}
              className={`flex-1 px-4 py-2 text-sm font-medium ${
                rightPanelTab === "timeline"
                  ? "text-accent border-b-2 border-accent"
                  : "text-foreground-muted hover:text-foreground"
              }`}
            >
              Timeline
            </button>
            <button
              onClick={() => setRightPanelTab("outputs")}
              className={`flex-1 px-4 py-2 text-sm font-medium ${
                rightPanelTab === "outputs"
                  ? "text-accent border-b-2 border-accent"
                  : "text-foreground-muted hover:text-foreground"
              }`}
            >
              Outputs
            </button>
          </div>

          {/* Tab Content */}
          <div className="flex-1 overflow-auto">
            {rightPanelTab === "timeline" && <ExecutionTimeline />}
            {rightPanelTab === "outputs" && <AgentOutputs />}
          </div>
        </div>
      </div>

      {/* Bottom Panel - Chat */}
      <ChatPanel projectId={projectId} />

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
