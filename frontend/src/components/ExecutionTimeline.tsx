"use client";

import { CheckCircle, Circle, Loader2, XCircle } from "lucide-react";
import { useProjectStore } from "@/lib/store";
import { cn, getAgentColor, getAgentBgColor } from "@/lib/utils";

interface TimelineAgent {
  id: string;
  name: string;
  label: string;
  description: string;
}

const agents: TimelineAgent[] = [
  {
    id: "manager",
    name: "Manager",
    label: "Requirements Analysis",
    description: "Converting prompt to structured requirements",
  },
  {
    id: "architect",
    name: "Architect",
    label: "System Design",
    description: "Designing architecture and file structure",
  },
  {
    id: "engineer",
    name: "Engineer",
    label: "Code Generation",
    description: "Generating production-ready code",
  },
  {
    id: "qa",
    name: "QA",
    label: "Quality Assurance",
    description: "Creating tests and validating quality",
  },
];

export function ExecutionTimeline() {
  const { project, pipelineRunning, currentAgent, progress } =
    useProjectStore();

  const getAgentStatus = (
    agentId: string,
  ): "pending" | "running" | "complete" | "error" => {
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

    // Check if output exists
    const outputMap: Record<string, boolean> = {
      manager: !!project.state.manager_output,
      architect: !!project.state.architect_output,
      engineer: !!project.state.engineer_output,
      qa: !!project.state.qa_output,
    };

    return outputMap[agentId] ? "complete" : "pending";
  };

  const getStatusIcon = (
    status: "pending" | "running" | "complete" | "error",
  ) => {
    switch (status) {
      case "complete":
        return <CheckCircle className="h-5 w-5 text-success" />;
      case "running":
        return <Loader2 className="h-5 w-5 text-accent animate-spin" />;
      case "error":
        return <XCircle className="h-5 w-5 text-error" />;
      default:
        return <Circle className="h-5 w-5 text-foreground-subtle" />;
    }
  };

  return (
    <div className="p-4 space-y-4">
      {/* Progress Bar */}
      <div className="space-y-2">
        <div className="flex justify-between text-sm">
          <span className="text-foreground-muted">Progress</span>
          <span className="font-medium">{Math.round(progress)}%</span>
        </div>
        <div className="h-2 bg-background-tertiary rounded-full overflow-hidden">
          <div
            className="h-full bg-accent transition-all duration-500 ease-out"
            style={{ width: `${progress}%` }}
          />
        </div>
      </div>

      {/* Timeline */}
      <div className="space-y-1">
        {agents.map((agent, index) => {
          const status = getAgentStatus(agent.id);
          const isLast = index === agents.length - 1;

          return (
            <div key={agent.id} className="relative">
              {/* Connector Line */}
              {!isLast && (
                <div
                  className={cn(
                    "absolute left-[9px] top-8 w-0.5 h-8",
                    status === "complete" ? "bg-success" : "bg-border",
                  )}
                />
              )}

              {/* Agent Card */}
              <div
                className={cn(
                  "flex items-start gap-3 p-3 rounded-lg transition-colors",
                  status === "running" && getAgentBgColor(agent.id),
                  status === "complete" && "opacity-80",
                )}
              >
                <div className="mt-0.5">{getStatusIcon(status)}</div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2">
                    <span
                      className={cn(
                        "font-medium text-sm",
                        status === "running" && getAgentColor(agent.id),
                      )}
                    >
                      {agent.name}
                    </span>
                    <span className="text-xs text-foreground-subtle">
                      {agent.label}
                    </span>
                  </div>
                  <p className="text-xs text-foreground-muted mt-0.5">
                    {agent.description}
                  </p>
                </div>
              </div>
            </div>
          );
        })}
      </div>

      {/* Summary */}
      {project?.state.pipeline_status?.stage === "completed" && (
        <div className="mt-4 p-3 bg-success/10 border border-success/20 rounded-lg">
          <div className="flex items-center gap-2 text-success text-sm font-medium">
            <CheckCircle className="h-4 w-4" />
            Pipeline Complete
          </div>
          <p className="text-xs text-foreground-muted mt-1">
            All agents have finished executing. Check the outputs tab for
            details.
          </p>
        </div>
      )}

      {project?.state.pipeline_status?.stage === "error" && (
        <div className="mt-4 p-3 bg-error/10 border border-error/20 rounded-lg">
          <div className="flex items-center gap-2 text-error text-sm font-medium">
            <XCircle className="h-4 w-4" />
            Pipeline Error
          </div>
          <p className="text-xs text-foreground-muted mt-1">
            {project.state.pipeline_status.message ||
              "An error occurred during execution."}
          </p>
        </div>
      )}
    </div>
  );
}
