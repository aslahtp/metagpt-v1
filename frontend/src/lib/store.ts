/**
 * Global state management using Zustand.
 */

import { create } from "zustand";
import type { Project, FileTreeNode, ChatMessage, GeneratedFile } from "./api";
import { DEFAULT_THEME } from "./editorThemes";

// Helper to safely read from localStorage
function getStoredTheme(): string {
  if (typeof window === "undefined") return DEFAULT_THEME;
  try {
    return localStorage.getItem("metagpt-editor-theme") || DEFAULT_THEME;
  } catch {
    return DEFAULT_THEME;
  }
}

interface ProjectStore {
  // Current project
  project: Project | null;
  setProject: (project: Project | null) => void;

  // Pipeline state
  pipelineRunning: boolean;
  setPipelineRunning: (running: boolean) => void;
  currentAgent: string | null;
  setCurrentAgent: (agent: string | null) => void;
  progress: number;
  setProgress: (progress: number) => void;

  // File explorer
  fileTree: FileTreeNode | null;
  setFileTree: (tree: FileTreeNode | null) => void;
  selectedFile: string | null;
  setSelectedFile: (path: string | null) => void;
  fileContent: string | null;
  setFileContent: (content: string | null) => void;
  fileLanguage: string | null;
  setFileLanguage: (language: string | null) => void;

  // Generated files (from engineer)
  generatedFiles: GeneratedFile[];
  setGeneratedFiles: (files: GeneratedFile[]) => void;
  addGeneratedFile: (file: GeneratedFile) => void;

  // Chat
  chatMessages: ChatMessage[];
  addChatMessage: (message: ChatMessage) => void;
  clearChatMessages: () => void;

  // Agent outputs visibility
  expandedAgents: Set<string>;
  toggleAgentExpanded: (agent: string) => void;

  // Preview
  previewEnabled: boolean;
  setPreviewEnabled: (enabled: boolean) => void;

  // Preview frame state
  previewInitialized: boolean;
  setPreviewInitialized: (initialized: boolean) => void;

  // Sandbox (E2B)
  sandboxUrl: string | null;
  setSandboxUrl: (url: string | null) => void;
  sandboxId: string | null;
  setSandboxId: (id: string | null) => void;
  sandboxLoading: boolean;
  setSandboxLoading: (loading: boolean) => void;

  // Editor theme
  editorTheme: string;
  setEditorTheme: (theme: string) => void;

  // File explorer settings
  hideNodeModules: boolean;
  setHideNodeModules: (hide: boolean) => void;

  // Reset
  reset: () => void;
}

export const useProjectStore = create<ProjectStore>((set) => ({
  // Project
  project: null,
  setProject: (project) => set({ project }),

  // Pipeline
  pipelineRunning: false,
  setPipelineRunning: (running) => set({ pipelineRunning: running }),
  currentAgent: null,
  setCurrentAgent: (agent) => set({ currentAgent: agent }),
  progress: 0,
  setProgress: (progress) => set({ progress }),

  // File explorer
  fileTree: null,
  setFileTree: (tree) => set({ fileTree: tree }),
  selectedFile: null,
  setSelectedFile: (path) => set({ selectedFile: path }),
  fileContent: null,
  setFileContent: (content) => set({ fileContent: content }),
  fileLanguage: null,
  setFileLanguage: (language) => set({ fileLanguage: language }),

  // Generated files
  generatedFiles: [],
  setGeneratedFiles: (files) => set({ generatedFiles: files }),
  addGeneratedFile: (file) =>
    set((state) => ({
      generatedFiles: [...state.generatedFiles, file],
    })),

  // Chat
  chatMessages: [],
  addChatMessage: (message) =>
    set((state) => ({
      chatMessages: [...state.chatMessages, message],
    })),
  clearChatMessages: () => set({ chatMessages: [] }),

  // Agent outputs
  expandedAgents: new Set(["manager", "architect", "engineer", "qa"]),
  toggleAgentExpanded: (agent) =>
    set((state) => {
      const newSet = new Set(state.expandedAgents);
      if (newSet.has(agent)) {
        newSet.delete(agent);
      } else {
        newSet.add(agent);
      }
      return { expandedAgents: newSet };
    }),

  // Preview
  previewEnabled: false,
  setPreviewEnabled: (enabled) => set({ previewEnabled: enabled }),

  // Preview frame state
  previewInitialized: false,
  setPreviewInitialized: (initialized) =>
    set({ previewInitialized: initialized }),

  // Sandbox (E2B)
  sandboxUrl: null,
  setSandboxUrl: (url) => set({ sandboxUrl: url }),
  sandboxId: null,
  setSandboxId: (id) => set({ sandboxId: id }),
  sandboxLoading: false,
  setSandboxLoading: (loading) => set({ sandboxLoading: loading }),

  // Editor theme (persisted to localStorage)
  editorTheme: getStoredTheme(),
  setEditorTheme: (theme) => {
    try {
      localStorage.setItem("metagpt-editor-theme", theme);
    } catch {}
    set({ editorTheme: theme });
  },

  // File explorer settings
  hideNodeModules: true,
  setHideNodeModules: (hide) => set({ hideNodeModules: hide }),

  // Reset
  reset: () =>
    set({
      project: null,
      pipelineRunning: false,
      currentAgent: null,
      progress: 0,
      fileTree: null,
      selectedFile: null,
      fileContent: null,
      fileLanguage: null,
      generatedFiles: [],
      chatMessages: [],
      expandedAgents: new Set(["manager", "architect", "engineer", "qa"]),
      previewEnabled: false,
      previewInitialized: false,
      sandboxUrl: null,
      sandboxId: null,
      sandboxLoading: false,
    }),
}));
