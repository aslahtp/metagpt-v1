"use client";

import { useEffect, useState, useCallback } from "react";
import { useParams } from "next/navigation";
import { Sparkles } from "lucide-react";
import {
  getProject,
  runPipeline,
  getFileTree,
  getFileContent,
} from "@/lib/api";
import { useProjectStore } from "@/lib/store";
import { ExecutionTimeline } from "@/components/ExecutionTimeline";
import { FileExplorer } from "@/components/FileExplorer";
import { CodeViewer } from "@/components/CodeViewer";
import { ChatPanel } from "@/components/ChatPanel";
import { AgentOutputs } from "@/components/AgentOutputs";
import { PreviewPanel } from "@/components/PreviewPanel";

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
    previewEnabled,
  } = useProjectStore();

  const [activeTab, setActiveTab] = useState<
    "timeline" | "outputs" | "preview"
  >("timeline");
  const [error, setError] = useState<string | null>(null);

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

  // Run pipeline
  const handleRunPipeline = async () => {
    if (pipelineRunning) return;

    setPipelineRunning(true);
    setError(null);
    setCurrentAgent("manager");
    setProgress(0);

    try {
      // Use polling approach for simplicity
      const pollStatus = async () => {
        const projectData = await getProject(projectId);
        setProject(projectData);

        const status = projectData.state.pipeline_status;
        if (status) {
          setProgress(status.progress);
          setCurrentAgent(status.current_agent);
        }

        // Check if completed or errored
        if (status?.stage === "completed" || status?.stage === "error") {
          setPipelineRunning(false);

          if (status.stage === "completed") {
            // Load file tree
            try {
              const tree = await getFileTree(projectId);
              setFileTree(tree.root);
            } catch {
              // Handle error
            }
          }
          return;
        }

        // Continue polling
        setTimeout(pollStatus, 1000);
      };

      // Start the pipeline
      await runPipeline(projectId);
      pollStatus();
    } catch (err) {
      setError("Pipeline execution failed");
      setPipelineRunning(false);
    }
  };

  // Fetch file content
  const handleSelectFile = async (path: string) => {
    setSelectedFile(path);

    try {
      const file = await getFileContent(projectId, path);
      setFileContent(file.content);
      setFileLanguage(file.language);
    } catch {
      setFileContent("// Failed to load file content");
      setFileLanguage("text");
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

  return (
    <div className="h-screen flex flex-col">
      {/* Header */}
      <header className="h-14 border-b border-border flex items-center px-4 gap-4 shrink-0">
        <div className="flex items-center gap-2">
          <Sparkles className="h-5 w-5 text-accent" />
          <span className="font-medium">MetaGPT-Lovable</span>
        </div>
        <div className="h-4 w-px bg-border" />
        <div className="flex-1 min-w-0">
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
          <div className="p-3 border-b border-border">
            <h2 className="text-sm font-medium">Files</h2>
          </div>
          <div className="flex-1 overflow-auto">
            <FileExplorer onSelectFile={handleSelectFile} />
          </div>
        </div>

        {/* Center Panel - Code Viewer */}
        <div className="flex-1 flex flex-col min-w-0">
          <CodeViewer />
        </div>

        {/* Right Panel - Timeline/Outputs/Preview */}
        <div className="w-96 border-l border-border flex flex-col shrink-0">
          {/* Tabs */}
          <div className="flex border-b border-border shrink-0">
            <button
              onClick={() => setActiveTab("timeline")}
              className={`flex-1 px-4 py-2 text-sm font-medium ${
                activeTab === "timeline"
                  ? "text-accent border-b-2 border-accent"
                  : "text-foreground-muted hover:text-foreground"
              }`}
            >
              Timeline
            </button>
            <button
              onClick={() => setActiveTab("outputs")}
              className={`flex-1 px-4 py-2 text-sm font-medium ${
                activeTab === "outputs"
                  ? "text-accent border-b-2 border-accent"
                  : "text-foreground-muted hover:text-foreground"
              }`}
            >
              Outputs
            </button>
            {project.preview?.preview_supported && (
              <button
                onClick={() => setActiveTab("preview")}
                className={`flex-1 px-4 py-2 text-sm font-medium ${
                  activeTab === "preview"
                    ? "text-accent border-b-2 border-accent"
                    : "text-foreground-muted hover:text-foreground"
                }`}
              >
                Preview
              </button>
            )}
          </div>

          {/* Tab Content */}
          <div className="flex-1 overflow-auto">
            {activeTab === "timeline" && <ExecutionTimeline />}
            {activeTab === "outputs" && <AgentOutputs />}
            {activeTab === "preview" && <PreviewPanel />}
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
