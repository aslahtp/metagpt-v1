"use client";

import { useState, useRef, useEffect } from "react";
import {
  Loader2,
  ChevronUp,
  ChevronDown,
  ImagePlus,
  Infinity,
  Zap,
  Check,
  FileCode,
  Database,
} from "lucide-react";
import { sendChatMessage, indexProjectFiles } from "@/lib/api";
import { useProjectStore } from "@/lib/store";
import { cn, formatDate, getAgentColor } from "@/lib/utils";

interface ChatPanelProps {
  projectId: string;
  /** When true, render as sidebar (no toggle bar, fills parent height) */
  embedded?: boolean;
  /** Called after chat edits modify/create files — parent can refresh file tree */
  onFilesModified?: (files: string[]) => void;
}

export function ChatPanel({ projectId, embedded = false, onFilesModified }: ChatPanelProps) {
  const [message, setMessage] = useState("");
  const {
    chatMessages,
    addChatMessage,
    chatLoading: isLoading,
    setChatLoading: setIsLoading,
    updateChatMessage,
    project,
    setProject,
    pendingChatInput,
    setPendingChatInput,
  } = useProjectStore();
  const [isExpanded, setIsExpanded] = useState(false);
  const [autoMode, setAutoMode] = useState(true);
  const [selectedModel, setSelectedModel] = useState<string | null>(null);
  const [modelDropdownOpen, setModelDropdownOpen] = useState(false);
  const inputRef = useRef<HTMLTextAreaElement>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const modelDropdownRef = useRef<HTMLDivElement>(null);

  const MODELS = [
    { id: "gemini-2.0-flash", label: "Gemini 3 Flash" },
    { id: "gemini-2.5-pro", label: "Gemini 3 Pro" },
  ] as const;

  // Close dropdown on outside click
  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (
        modelDropdownRef.current &&
        !modelDropdownRef.current.contains(e.target as Node)
      ) {
        setModelDropdownOpen(false);
      }
    };
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  const handleToggleAuto = () => {
    if (autoMode) {
      // Turning Auto OFF — don't select a model yet, just open dropdown
      setAutoMode(false);
      setSelectedModel(null);
      setModelDropdownOpen(true);
    } else {
      // Turning Auto ON — clear manual selection
      setAutoMode(true);
      setSelectedModel(null);
      setModelDropdownOpen(false);
    }
  };

  const handleSelectModel = (modelId: string) => {
    setSelectedModel(modelId);
    setAutoMode(false);
    setModelDropdownOpen(false);
  };

  const getDisplayLabel = () => {
    if (autoMode) return "Auto";
    const found = MODELS.find((m) => m.id === selectedModel);
    return found ? found.label : "Auto";
  };



  // Consume pendingChatInput set by other components (e.g. QA "Fix" button)
  useEffect(() => {
    if (pendingChatInput) {
      setMessage(pendingChatInput);
      setPendingChatInput(null);
      setIsExpanded(true);
      setTimeout(() => inputRef.current?.focus(), 50);
    }
  }, [pendingChatInput, setPendingChatInput]);

  // Scroll to bottom when new messages arrive
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [chatMessages]);

  // Adaptive textarea height (min 1 line, max ~6 lines)
  const MIN_TEXTAREA_HEIGHT = 40;
  const MAX_TEXTAREA_HEIGHT = 160;

  const adjustTextareaHeight = () => {
    const el = inputRef.current;
    if (!el) return;
    el.style.height = "auto";
    const h = Math.min(
      Math.max(el.scrollHeight, MIN_TEXTAREA_HEIGHT),
      MAX_TEXTAREA_HEIGHT
    );
    el.style.height = `${h}px`;
  };

  useEffect(() => {
    adjustTextareaHeight();
  }, [message]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!message.trim() || isLoading) return;

    const userMessage = message.trim();
    setMessage("");
    setIsLoading(true);

    // Add user message
    addChatMessage({
      id: Date.now().toString(),
      role: "user",
      content: userMessage,
      timestamp: new Date().toISOString(),
      files_modified: [],
    });

    try {
      const response = await sendChatMessage(
        projectId,
        userMessage,
        autoMode ? null : selectedModel,
      );

      // Add assistant response — merge files_referenced from the response
      addChatMessage({
        ...response.message,
        files_referenced: response.files_referenced,
        indexing_status: response.indexing_status,
      });

      // If indexing is pending, trigger it live
      if (response.indexing_status === "pending") {
        // Optimistically update message to show indexing spinner
        const indexingMsgId = response.message.id;
        updateChatMessage(indexingMsgId, { indexing_status: "indexing" });

        // Trigger indexing in background
        indexProjectFiles(projectId, response.files_modified)
          .then(() => {
            updateChatMessage(indexingMsgId, { indexing_status: "completed" });
          })
          .catch(() => {
            updateChatMessage(indexingMsgId, { indexing_status: "failed" });
          });
      }

      // Notify parent to refresh file tree + code viewer
      if (response.project_updated && response.files_modified.length > 0) {
        onFilesModified?.(response.files_modified);
      }
    } catch (error) {
      addChatMessage({
        id: Date.now().toString(),
        role: "assistant",
        content: "Sorry, I encountered an error processing your request.",
        timestamp: new Date().toISOString(),
        files_modified: [],
      });
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  const showContent = embedded || isExpanded;

  return (
    <div
      className={cn(
        "flex flex-col",
        embedded
          ? "h-full min-h-0"
          : cn(
              "border-t border-border transition-all duration-300",
              isExpanded ? "h-80" : "h-14",
            ),
      )}
    >
      {/* Toggle Bar (only when not embedded) */}
      {!embedded && (
        <button
          onClick={() => setIsExpanded(!isExpanded)}
          className="w-full h-10 px-4 flex items-center justify-between hover:bg-background-secondary transition-colors"
        >
          <span className="text-sm font-medium">Chat</span>
          <div className="flex items-center gap-2">
            {chatMessages.length > 0 && (
              <span className="text-xs text-foreground-muted">
                {chatMessages.length} messages
              </span>
            )}
            {isExpanded ? (
              <ChevronDown className="h-4 w-4 text-foreground-muted" />
            ) : (
              <ChevronUp className="h-4 w-4 text-foreground-muted" />
            )}
          </div>
        </button>
      )}

      {/* Chat Content */}
      {showContent && (
        <div className={cn("flex flex-col", embedded ? "flex-1 min-h-0" : "h-[calc(100%-40px)]")}>
          {/* Messages */}
          <div className="flex-1 min-h-0 overflow-y-auto overflow-x-hidden px-4 py-2 space-y-3">
            {chatMessages.length === 0 ? (
              <div className="text-center text-foreground-muted text-sm py-4">
                <p>Ask questions or request changes to your project.</p>
                <p className="text-xs text-foreground-subtle mt-1">
                  The system will determine which agents need to run.
                </p>
              </div>
            ) : (
              <>
                {chatMessages.map((msg) => (
                  <div
                    key={msg.id}
                    className={cn(
                      "flex gap-3 animate-message-in",
                      msg.role === "user" ? "justify-end" : "justify-start",
                    )}
                  >
                    <div
                      className={cn(
                        "max-w-[80%] rounded-2xl px-3 py-2 overflow-hidden",
                        msg.role === "user"
                          ? "bg-foreground text-background rounded-br-sm"
                          : "bg-background-tertiary rounded-bl-sm",
                      )}
                    >
                      <p className="text-sm whitespace-pre-wrap break-words">{msg.content}</p>
                      <div className="flex items-center gap-2 mt-1">
                        <span className="text-xs opacity-60">
                          {formatDate(msg.timestamp)}
                        </span>
                        {msg.agent_triggered && (
                          <span
                            className={cn(
                              "text-xs",
                              getAgentColor(msg.agent_triggered),
                            )}
                          >
                            via {msg.agent_triggered}
                          </span>
                        )}
                      </div>
                      {msg.files_modified.length > 0 && (
                        <div className="mt-2 text-xs opacity-80 break-all">
                          Modified: {msg.files_modified.join(", ")}
                        </div>
                      )}
                      {msg.role === "assistant" &&
                        msg.files_referenced &&
                        msg.files_referenced.length > 0 && (
                          <div className="mt-1.5 flex items-center gap-1 text-xs text-foreground-muted">
                            <FileCode className="h-3 w-3" />
                            <span>
                              Referenced {msg.files_referenced.length} file
                              {msg.files_referenced.length !== 1 ? "s" : ""}
                            </span>
                          </div>
                        )}
                      {msg.role === "assistant" && msg.indexing_status === "indexing" && (
                        <div className="mt-1.5 flex items-center gap-1 text-xs text-foreground-muted animate-pulse">
                          <Loader2 className="h-3 w-3 animate-spin" />
                          <span>Indexing codebase...</span>
                        </div>
                      )}
                      {msg.role === "assistant" && msg.indexing_status === "completed" && (
                        <div className="mt-1.5 flex items-center gap-1 text-xs text-success/80">
                          <Check className="h-3 w-3" />
                          <span>Re-indexed codebase</span>
                        </div>
                      )}
                      {msg.role === "assistant" && msg.indexing_status === "failed" && (
                        <div className="mt-1.5 flex items-center gap-1 text-xs text-destructive/80">
                          <Database className="h-3 w-3" />
                          <span>Indexing failed</span>
                        </div>
                      )}
                    </div>
                  </div>
                ))}
                {isLoading && (
                  <div className="flex justify-start">
                    <div className="rounded-2xl rounded-bl-sm px-3.5 py-2.5 bg-background-tertiary">
                      <div className="flex items-center gap-1.5">
                        <span
                          className="animate-dot-pulse inline-block w-1.5 h-1.5 rounded-full bg-foreground-muted"
                          style={{ animationDelay: "0ms" }}
                        />
                        <span
                          className="animate-dot-pulse inline-block w-1.5 h-1.5 rounded-full bg-foreground-muted"
                          style={{ animationDelay: "160ms" }}
                        />
                        <span
                          className="animate-dot-pulse inline-block w-1.5 h-1.5 rounded-full bg-foreground-muted"
                          style={{ animationDelay: "320ms" }}
                        />
                      </div>
                    </div>
                  </div>
                )}
              </>
            )}
            <div ref={messagesEndRef} />
          </div>

          {/* Input — single rounded chatbox with text area + bottom bar */}
          <form onSubmit={handleSubmit} className="px-4 py-2 w-full">
            <div className="rounded-xl border border-border bg-background-secondary overflow-visible flex flex-col">
              {/* Text area — upper part, no inner border */}
              <textarea
                ref={inputRef}
                value={message}
                onChange={(e) => setMessage(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder="Type something..."
                className="w-full resize-none overflow-y-auto px-4 pt-3 pb-0 bg-transparent text-foreground placeholder:text-foreground-subtle text-sm focus:outline-none min-h-[44px] max-h-[160px]"
                rows={1}
                disabled={isLoading}
              />
              {/* Bottom control bar */}
              <div className="flex items-center justify-between px-3 py-1 min-h-[32px]">
                <div className="flex items-center gap-1">
                  <button
                    type="button"
                    className="flex items-center gap-0.5 px-2 py-1.5 rounded-md text-foreground-muted hover:text-foreground hover:bg-background-tertiary text-xs font-medium transition-colors"
                    title="Context length"
                  >
                    <Infinity className="h-3.5 w-3.5" />
                    <ChevronDown className="h-3 w-3" />
                  </button>

                  {/* Model selector with Auto toggle */}
                  <div className="relative" ref={modelDropdownRef}>
                    <button
                      type="button"
                      onClick={() => setModelDropdownOpen(!modelDropdownOpen)}
                      className="flex items-center gap-1 px-2 py-1.5 rounded-md text-xs font-medium text-foreground-muted hover:text-foreground hover:bg-background-tertiary transition-colors"
                      title="Model selection"
                    >
                      {getDisplayLabel()}
                      <ChevronDown className="h-3 w-3" />
                    </button>

                    {modelDropdownOpen && (
                      <div className="absolute bottom-full left-0 mb-1 w-48 rounded-lg border border-border bg-background-secondary shadow-lg pt-2 pb-2 z-[100]">
                        {/* Auto option */}
                        <button
                          type="button"
                          onClick={handleToggleAuto}
                          className="w-full flex items-center gap-2 px-3 py-2 text-xs font-medium text-foreground-muted hover:text-foreground hover:bg-background-tertiary transition-colors"
                        >
                          <Zap className="h-3.5 w-3.5" />
                          <span className="flex-1 text-left">Auto</span>
                          {autoMode && <Check className="h-3.5 w-3.5" />}
                        </button>

                        <div className="h-px bg-border my-1" />

                        {/* Model options */}
                        {MODELS.map((model) => (
                          <button
                            key={model.id}
                            type="button"
                            onClick={() => handleSelectModel(model.id)}
                            className="w-full flex items-center gap-2 px-3 py-2 text-xs font-medium text-foreground-muted hover:text-foreground hover:bg-background-tertiary transition-colors"
                          >
                            <span className="flex-1 text-left">{model.label}</span>
                            {!autoMode && selectedModel === model.id && (
                              <Check className="h-3.5 w-3.5" />
                            )}
                          </button>
                        ))}
                      </div>
                    )}
                  </div>
                </div>
                <div className="flex items-center gap-0.5">
                  <button
                    type="button"
                    className="p-2 rounded-md text-foreground-muted hover:text-foreground hover:bg-background-tertiary transition-colors"
                    title="Attach image"
                  >
                    <ImagePlus className="h-4 w-4" />
                  </button>
                  <button
                    type="submit"
                    disabled={!message.trim() || isLoading}
                    className={cn(
                      "h-8 w-8 rounded-full flex items-center justify-center transition-all duration-200 ml-0.5",
                      message.trim() && !isLoading
                        ? "bg-foreground text-background hover:bg-accent-hover"
                        : "bg-foreground-subtle/20 text-foreground-subtle disabled:opacity-40 disabled:pointer-events-none"
                    )}
                    title="Send"
                  >
                    {isLoading ? (
                      <Loader2 className="h-4 w-4 animate-spin" />
                    ) : (
                      <span
                        className="material-symbols-outlined text-[18px] leading-none"
                        aria-hidden
                      >
                        send
                      </span>
                    )}
                  </button>
                </div>
              </div>
            </div>
          </form>
        </div>
      )}
    </div>
  );
}
