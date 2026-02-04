"use client";

import { useState, useRef, useEffect } from "react";
import { Send, Loader2, ChevronUp, ChevronDown } from "lucide-react";
import { sendChatMessage } from "@/lib/api";
import { useProjectStore } from "@/lib/store";
import { cn, formatDate, getAgentColor } from "@/lib/utils";

interface ChatPanelProps {
  projectId: string;
}

export function ChatPanel({ projectId }: ChatPanelProps) {
  const [message, setMessage] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [isExpanded, setIsExpanded] = useState(false);
  const inputRef = useRef<HTMLTextAreaElement>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const { chatMessages, addChatMessage, project, setProject } =
    useProjectStore();

  // Scroll to bottom when new messages arrive
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [chatMessages]);

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
      const response = await sendChatMessage(projectId, userMessage);

      // Add assistant response
      addChatMessage(response.message);

      // Refresh project if updated
      if (response.project_updated) {
        // The store will be updated by the parent component
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

  return (
    <div
      className={cn(
        "border-t border-border transition-all duration-300",
        isExpanded ? "h-80" : "h-14",
      )}
    >
      {/* Toggle Bar */}
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

      {/* Chat Content */}
      {isExpanded && (
        <div className="h-[calc(100%-40px)] flex flex-col">
          {/* Messages */}
          <div className="flex-1 overflow-auto px-4 py-2 space-y-3">
            {chatMessages.length === 0 ? (
              <div className="text-center text-foreground-muted text-sm py-4">
                <p>Ask questions or request changes to your project.</p>
                <p className="text-xs text-foreground-subtle mt-1">
                  The system will determine which agents need to run.
                </p>
              </div>
            ) : (
              chatMessages.map((msg) => (
                <div
                  key={msg.id}
                  className={cn(
                    "flex gap-3 animate-fade-in",
                    msg.role === "user" ? "justify-end" : "justify-start",
                  )}
                >
                  <div
                    className={cn(
                      "max-w-[80%] rounded-lg px-3 py-2",
                      msg.role === "user"
                        ? "bg-accent text-white"
                        : "bg-background-tertiary",
                    )}
                  >
                    <p className="text-sm whitespace-pre-wrap">{msg.content}</p>
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
                      <div className="mt-2 text-xs opacity-80">
                        Modified: {msg.files_modified.join(", ")}
                      </div>
                    )}
                  </div>
                </div>
              ))
            )}
            <div ref={messagesEndRef} />
          </div>

          {/* Input */}
          <form
            onSubmit={handleSubmit}
            className="px-4 py-2 border-t border-border"
          >
            <div className="flex items-end gap-2">
              <textarea
                ref={inputRef}
                value={message}
                onChange={(e) => setMessage(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder="Ask a question or request changes..."
                className="flex-1 resize-none px-3 py-2 rounded-lg border border-border bg-background-secondary text-sm focus:outline-none focus:ring-2 focus:ring-accent"
                rows={1}
                disabled={isLoading}
              />
              <button
                type="submit"
                disabled={!message.trim() || isLoading}
                className="btn-primary h-9 w-9 p-0 flex items-center justify-center"
              >
                {isLoading ? (
                  <Loader2 className="h-4 w-4 animate-spin" />
                ) : (
                  <Send className="h-4 w-4" />
                )}
              </button>
            </div>
          </form>
        </div>
      )}
    </div>
  );
}
