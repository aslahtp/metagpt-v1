/**
 * API client for MetaGPT backend.
 */

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "";

export interface Project {
  id: string;
  prompt: string;
  name: string;
  description: string;
  state: ProjectState;
  preview: PreviewMetadata;
  created_at: string;
  updated_at: string;
  version: number;
}

export interface ProjectState {
  manager_output: ManagerOutput | null;
  architect_output: ArchitectOutput | null;
  engineer_output: EngineerOutput | null;
  qa_output: QAOutput | null;
  pipeline_status: PipelineStatus;
}

export interface PipelineStatus {
  stage: string;
  progress: number;
  current_agent: string | null;
  message: string;
  started_at: string | null;
  completed_at: string | null;
}

export interface PreviewMetadata {
  is_react_project: boolean;
  is_nextjs_project: boolean;
  entry_file: string | null;
  preview_supported: boolean;
  framework: string | null;
}

export interface ManagerOutput {
  project_name: string;
  project_description: string;
  project_type: string;
  tech_stack: string[];
  requirements: Requirement[];
  constraints: string[];
  assumptions: string[];
  reasoning: string;
}

export interface Requirement {
  id: string;
  category: string;
  description: string;
  priority: string;
  acceptance_criteria: string[];
}

export interface ArchitectOutput {
  architecture_type: string;
  components: Component[];
  file_structure: FileStructure[];
  data_flow: string;
  api_design: Record<string, unknown>;
  database_schema: Record<string, unknown>;
  deployment_notes: string;
  reasoning: string;
}

export interface Component {
  name: string;
  type: string;
  description: string;
  technologies: string[];
  files: FileStructure[];
}

export interface FileStructure {
  path: string;
  purpose: string;
  dependencies: string[];
}

export interface EngineerOutput {
  files: GeneratedFile[];
  implementation_notes: string;
  dependencies_added: string[];
  setup_instructions: string[];
  reasoning: string;
}

export interface GeneratedFile {
  file_path: string;
  file_content: string;
  file_language: string;
  file_purpose: string;
}

export interface QAOutput {
  test_cases: TestCase[];
  validation_notes: ValidationNote[];
  code_review_summary: string;
  test_coverage_estimate: string;
  quality_score: number;
  approval_status: string;
  reasoning: string;
}

export interface TestCase {
  id: string;
  name: string;
  description: string;
  test_type: string;
  target_file: string;
  test_code: string;
  steps: string[];
  expected_result: string;
}

export interface ValidationNote {
  severity: string;
  category: string;
  file_path: string;
  description: string;
  recommendation: string;
}

export interface FileTreeNode {
  name: string;
  path: string;
  type: "file" | "directory";
  language?: string;
  children: FileTreeNode[];
}

export interface FileTree {
  project_id: string;
  root: FileTreeNode;
  total_files: number;
  total_directories: number;
}

export interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  timestamp: string;
  agent_triggered?: string;
  files_modified: string[];
}

// API Functions

export async function createProject(prompt: string): Promise<Project> {
  const res = await fetch(`${API_BASE}/api/v1/projects`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ prompt }),
  });
  if (!res.ok) throw new Error("Failed to create project");
  return res.json();
}

export async function getProject(projectId: string): Promise<Project> {
  const res = await fetch(`${API_BASE}/api/v1/projects/${projectId}`);
  if (!res.ok) throw new Error("Project not found");
  return res.json();
}

export async function runPipeline(projectId: string): Promise<Project> {
  const res = await fetch(`${API_BASE}/api/v1/pipeline/${projectId}/run`, {
    method: "POST",
  });
  if (!res.ok) throw new Error("Failed to run pipeline");
  return res.json();
}

export async function getFileTree(projectId: string): Promise<FileTree> {
  const res = await fetch(`${API_BASE}/api/v1/files/${projectId}/tree`);
  if (!res.ok) throw new Error("Failed to get file tree");
  return res.json();
}

export async function getFileContent(
  projectId: string,
  filePath: string
): Promise<{ path: string; content: string; language: string }> {
  // Remove leading slash if present and don't encode slashes
  const cleanPath = filePath.replace(/^\/+/, "");
  const res = await fetch(
    `${API_BASE}/api/v1/files/${projectId}/content/${cleanPath}`
  );
  if (!res.ok) throw new Error("Failed to get file content");
  return res.json();
}

export async function sendChatMessage(
  projectId: string,
  message: string,
  model?: string | null
): Promise<{
  message: ChatMessage;
  agents_executed: string[];
  files_modified: string[];
  project_updated: boolean;
}> {
  const body: Record<string, unknown> = { message };
  if (model) {
    body.model = model;
  }
  const res = await fetch(`${API_BASE}/api/v1/chat/${projectId}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!res.ok) throw new Error("Failed to send message");
  return res.json();
}

export async function getPipelineArtifacts(
  projectId: string
): Promise<{ project_id: string; artifacts: Record<string, unknown> }> {
  const res = await fetch(`${API_BASE}/api/v1/pipeline/${projectId}/artifacts`);
  if (!res.ok) throw new Error("Failed to get artifacts");
  return res.json();
}

export async function downloadProjectZip(projectId: string): Promise<void> {
  const res = await fetch(`${API_BASE}/api/v1/files/${projectId}/download`);
  if (!res.ok) throw new Error("Failed to download project");

  const blob = await res.blob();

  // Extract filename from Content-Disposition header, fallback to project id
  const disposition = res.headers.get("Content-Disposition");
  let filename = `${projectId}.zip`;
  if (disposition) {
    const match = disposition.match(/filename="?([^"]+)"?/);
    if (match) filename = match[1];
  }

  // Create a temporary link to trigger the browser download
  const url = window.URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  a.remove();
  window.URL.revokeObjectURL(url);
}

export async function streamPipeline(
  projectId: string,
  onEvent: (event: { type: string; data: Record<string, unknown> }) => void,
  onError: (error: Error) => void
): Promise<void> {
  const res = await fetch(`${API_BASE}/api/v1/pipeline/${projectId}/stream`, {
    method: "POST",
  });

  if (!res.ok) {
    onError(new Error("Failed to start pipeline stream"));
    return;
  }

  if (!res.body) {
    onError(new Error("No response body from stream"));
    return;
  }

  const reader = res.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  try {
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });

      // SSE events are separated by double newlines
      const parts = buffer.split("\n\n");
      buffer = parts.pop() || "";

      for (const part of parts) {
        if (!part.trim()) continue;

        let eventType = "message";
        const dataLines: string[] = [];

        for (const line of part.split("\n")) {
          if (line.startsWith("event:")) {
            eventType = line.slice(6).trim();
          } else if (line.startsWith("data:")) {
            dataLines.push(line.slice(5).trim());
          }
          // Ignore comments (lines starting with :) and other fields
        }

        if (dataLines.length > 0) {
          const data = dataLines.join("\n");
          try {
            const parsed = JSON.parse(data);
            onEvent({ type: eventType, data: parsed });
          } catch {
            console.error("Failed to parse SSE data:", data);
          }
        }
      }
    }
  } catch (err) {
    onError(err instanceof Error ? err : new Error("Stream connection error"));
  }
}
