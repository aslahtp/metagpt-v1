/**
 * Global state management using Zustand.
 */

import { create } from "zustand";
import type { Project, FileTreeNode, ChatMessage, GeneratedFile } from "./api";
import { DEFAULT_THEME } from "./editorThemes";

// Helper to safely read editor theme from localStorage,
// with UI-theme-aware defaults.
function getStoredTheme(): string {
  if (typeof window === "undefined") return DEFAULT_THEME;
  try {
    const storedEditor = localStorage.getItem("metagpt-editor-theme");
    if (storedEditor) return storedEditor;

    // No explicit editor theme set – fall back based on UI theme
    const uiTheme = localStorage.getItem("metagpt-ui-theme");
    if (uiTheme === "light") {
      // Light UI → use built-in VS Light
      return "vs";
    }

    // Dark (or unset) UI → use MetaGPT home dark theme
    return "metagpt-home";
  } catch {
    return DEFAULT_THEME;
  }
}

function getStoredUiTheme(): "dark" | "light" {
  if (typeof window === "undefined") return "dark";
  try {
    const stored = localStorage.getItem("metagpt-ui-theme");
    return stored === "light" ? "light" : "dark";
  } catch {
    return "dark";
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
  chatLoading: boolean;
  setChatLoading: (loading: boolean) => void;
  updateChatMessage: (id: string, updates: Partial<ChatMessage>) => void;

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
  sandboxLogs: string[];
  setSandboxLogs: (logs: string[]) => void;
  addSandboxLog: (log: string) => void;

  // Editor theme
  editorTheme: string;
  setEditorTheme: (theme: string) => void;

  // UI theme (light/dark)
  uiTheme: "dark" | "light";
  setUiTheme: (theme: "dark" | "light") => void;

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
  chatLoading: false,
  setChatLoading: (loading) => set({ chatLoading: loading }),
  updateChatMessage: (id, updates) =>
    set((state) => ({
      chatMessages: state.chatMessages.map((m) =>
        m.id === id ? { ...m, ...updates } : m
      ),
    })),

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
  sandboxLogs: [],
  setSandboxLogs: (logs) => set({ sandboxLogs: logs }),
  addSandboxLog: (log) =>
    set((state) => ({ sandboxLogs: [...state.sandboxLogs, log] })),

  // Editor theme (persisted to localStorage)
  editorTheme: getStoredTheme(),
  setEditorTheme: (theme) => {
    try {
      localStorage.setItem("metagpt-editor-theme", theme);
    } catch {}
    set({ editorTheme: theme });
  },

  // UI theme (persisted to localStorage)
  uiTheme: getStoredUiTheme(),
  setUiTheme: (theme) => {
    try {
      localStorage.setItem("metagpt-ui-theme", theme);
    } catch {}

    // Keep Monaco editor theme in sync with UI theme
    // when using one of the default themes.
    set((state) => {
      let nextEditorTheme = state.editorTheme;

      if (state.editorTheme === "metagpt-home" || state.editorTheme === "vs") {
        nextEditorTheme = theme === "light" ? "vs" : "metagpt-home";
      }

      return {
        uiTheme: theme,
        editorTheme: nextEditorTheme,
      };
    });
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
      chatLoading: false,
      expandedAgents: new Set(["manager", "architect", "engineer", "qa"]),
      previewEnabled: false,
      previewInitialized: false,
      sandboxUrl: null,
      sandboxId: null,
      sandboxLoading: false,
      sandboxLogs: [],
    }),
}));
