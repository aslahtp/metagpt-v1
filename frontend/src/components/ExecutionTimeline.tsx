"use client";

import { Check, Loader2, X, Circle } from "lucide-react";
import { useProjectStore } from "@/lib/store";
import { cn } from "@/lib/utils";

interface TimelineAgent {
  id: string;
  name: string;
  label: string;
  description: string;
  step: number;
}

const agents: TimelineAgent[] = [
  {
    id: "manager",
    name: "Manager",
    label: "Requirements",
    description: "Converting prompt to structured requirements",
    step: 1,
  },
  {
    id: "architect",
    name: "Architect",
    label: "Design",
    description: "Designing architecture and file structure",
    step: 2,
  },
  {
    id: "engineer",
    name: "Engineer",
    label: "Code Gen",
    description: "Generating production-ready code",
    step: 3,
  },
  {
    id: "qa",
    name: "QA",
    label: "Quality",
    description: "Creating tests and validating quality",
    step: 4,
  },
];

type AgentStatus = "pending" | "running" | "complete" | "error";

export function ExecutionTimeline() {
  const { project, pipelineRunning, currentAgent, progress } =
    useProjectStore();

  const getAgentStatus = (agentId: string): AgentStatus => {
    if (!project) return "pending";

    const stage = project.state.pipeline_status?.stage;
    const agentOrder = ["manager", "architect", "engineer", "qa"];
    const currentIndex = agentOrder.indexOf(currentAgent?.toLowerCase() || "");
    const agentIndex = agentOrder.indexOf(agentId);

    if (stage === "error" && currentAgent?.toLowerCase() === agentId) {
      return "error";
    }

    if (stage === "completed") {
      return "complete";
    }

    if (pipelineRunning) {
      if (agentIndex < currentIndex) return "complete";
      if (agentIndex === currentIndex) return "running";
      return "pending";
    }

    const outputMap: Record<string, boolean> = {
      manager: !!project.state.manager_output,
      architect: !!project.state.architect_output,
      engineer: !!project.state.engineer_output,
      qa: !!project.state.qa_output,
    };

    return outputMap[agentId] ? "complete" : "pending";
  };

  const allComplete =
    project?.state.pipeline_status?.stage === "completed";
  const hasError =
    project?.state.pipeline_status?.stage === "error";

  return (
    <div className="p-4 space-y-5">
      {/* Progress */}
      <div className="space-y-2">
        <div className="flex justify-between items-center">
          <span className="text-xs font-medium text-foreground-muted">
            Progress
          </span>
          <span
            className={cn(
              "text-xs font-semibold tabular-nums",
              allComplete
                ? "text-success"
                : hasError
                ? "text-error"
                : "text-foreground",
            )}
          >
            {Math.round(progress)}%
          </span>
        </div>
        <div className="h-1.5 bg-background-tertiary rounded-full overflow-hidden">
          <div
            className={cn(
              "h-full rounded-full transition-all duration-700 ease-out",
              allComplete
                ? "bg-success"
                : hasError
                ? "bg-error"
                : "bg-foreground",
            )}
            style={{ width: `${progress}%` }}
          />
        </div>
      </div>

      {/* Timeline */}
      <div className="relative">
        <div className="space-y-1">
          {agents.map((agent, index) => {
            const status = getAgentStatus(agent.id);
            const isLast = index === agents.length - 1;
            const prevStatus = index > 0 ? getAgentStatus(agents[index - 1].id) : null;

            return (
              <div key={agent.id} className="relative flex items-start gap-3">
                {/* Connector line to next agent */}
                {!isLast && (
                  <div
                    className={cn(
                      "absolute left-[14px] top-[36px] bottom-[-4px] z-0 transition-colors duration-300",
                      status === "complete"
                        ? "w-[2px] bg-white/60"
                        : "w-px bg-border",
                    )}
                  />
                )}
                {/* Step indicator */}
                <div className="relative z-10 shrink-0 mt-[2px]">
                  {/* Solid mask to hide the line behind the circle */}
                  <div className="absolute inset-[-4px] rounded-full bg-background" />
                  <div
                    className={cn(
                      "relative w-[30px] h-[30px] rounded-full flex items-center justify-center transition-all duration-300 bg-background",
                      status === "complete" &&
                        "ring-2 ring-success/40",
                      status === "running" &&
                        "ring-2 ring-foreground/25",
                      status === "error" &&
                        "ring-2 ring-error/40",
                      status === "pending" &&
                        "ring-1 ring-border",
                    )}
                  >
                    {status === "complete" && (
                      <Check className="h-3.5 w-3.5 text-success" strokeWidth={2.5} />
                    )}
                    {status === "running" && (
                      <Loader2 className="h-3.5 w-3.5 text-foreground animate-spin" />
                    )}
                    {status === "error" && (
                      <X className="h-3.5 w-3.5 text-error" strokeWidth={2.5} />
                    )}
                    {status === "pending" && (
                      <span className="text-[10px] font-semibold text-foreground-subtle">
                        {agent.step}
                      </span>
                    )}
                  </div>
                </div>

                {/* Content */}
                <div
                  className={cn(
                    "flex-1 min-w-0 py-1.5 pr-2",
                  )}
                >
                  <div className="flex items-baseline gap-2">
                    <span
                      className={cn(
                        "text-[13px] font-semibold leading-tight",
                        status === "complete" && "text-foreground",
                        status === "running" && "text-foreground",
                        status === "error" && "text-error",
                        status === "pending" && "text-foreground-subtle",
                      )}
                    >
                      {agent.name}
                    </span>
                    <span
                      className={cn(
                        "text-[11px] leading-tight",
                        status === "pending"
                          ? "text-foreground-subtle/60"
                          : "text-foreground-subtle",
                      )}
                    >
                      {agent.label}
                    </span>
                  </div>
                  <p
                    className={cn(
                      "text-[11px] mt-0.5 leading-relaxed",
                      status === "pending"
                        ? "text-foreground-subtle/50"
                        : "text-foreground-muted/70",
                    )}
                  >
                    {status === "running"
                      ? `${agent.description}...`
                      : agent.description}
                  </p>
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Status Banner */}
      {allComplete && (
        <div className="p-3 bg-success/5 border border-success/15 rounded-lg">
          <div className="flex items-center gap-2">
            <div className="w-5 h-5 rounded-full bg-success/15 flex items-center justify-center">
              <Check className="h-3 w-3 text-success" strokeWidth={2.5} />
            </div>
            <span className="text-xs font-semibold text-success">
              Pipeline Complete
            </span>
          </div>
          <p className="text-[11px] text-foreground-muted/70 mt-1.5 ml-7">
            All agents finished. Check the Outputs tab for details.
          </p>
        </div>
      )}

      {hasError && (
        <div className="p-3 bg-error/5 border border-error/15 rounded-lg">
          <div className="flex items-center gap-2">
            <div className="w-5 h-5 rounded-full bg-error/15 flex items-center justify-center">
              <X className="h-3 w-3 text-error" strokeWidth={2.5} />
            </div>
            <span className="text-xs font-semibold text-error">
              Pipeline Error
            </span>
          </div>
          <p className="text-[11px] text-foreground-muted/70 mt-1.5 ml-7">
            {project?.state.pipeline_status?.message ||
              "An error occurred during execution."}
          </p>
        </div>
      )}
    </div>
  );
}
