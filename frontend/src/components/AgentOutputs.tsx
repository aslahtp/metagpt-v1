"use client";

import { useState } from "react";
import {
  ChevronDown,
  ChevronRight,
  CheckCircle,
  AlertTriangle,
  AlertCircle,
  Info,
} from "lucide-react";
import { useProjectStore } from "@/lib/store";
import {
  cn,
  getAgentColor,
  getAgentBgColor,
  getPriorityColor,
  getSeverityColor,
} from "@/lib/utils";

export function AgentOutputs() {
  const { project, expandedAgents, toggleAgentExpanded } = useProjectStore();

  if (!project) {
    return (
      <div className="p-4 text-center text-foreground-muted text-sm">
        No project loaded.
      </div>
    );
  }

  const { manager_output, architect_output, engineer_output, qa_output } =
    project.state;

  return (
    <div className="p-2 space-y-2">
      {/* Manager Output */}
      <AgentSection
        id="manager"
        name="Manager"
        hasOutput={!!manager_output}
        isExpanded={expandedAgents.has("manager")}
        onToggle={() => toggleAgentExpanded("manager")}
      >
        {manager_output && (
          <div className="space-y-3">
            <InfoRow label="Project Name" value={manager_output.project_name} />
            <InfoRow label="Type" value={manager_output.project_type} />
            <InfoRow
              label="Tech Stack"
              value={manager_output.tech_stack.join(", ")}
            />

            {/* Requirements */}
            <div>
              <h4 className="text-xs font-medium text-foreground-muted mb-2">
                Requirements ({manager_output.requirements.length})
              </h4>
              <div className="space-y-1">
                {manager_output.requirements.slice(0, 5).map((req) => (
                  <div
                    key={req.id}
                    className="text-xs p-2 bg-background-tertiary rounded"
                  >
                    <div className="flex items-center gap-2">
                      <span className="text-foreground-subtle">{req.id}</span>
                      <span className={getPriorityColor(req.priority)}>
                        {req.priority}
                      </span>
                    </div>
                    <p className="mt-1">{req.description}</p>
                  </div>
                ))}
                {manager_output.requirements.length > 5 && (
                  <p className="text-xs text-foreground-subtle">
                    +{manager_output.requirements.length - 5} more requirements
                  </p>
                )}
              </div>
            </div>

            {/* Reasoning */}
            <ReasoningBlock text={manager_output.reasoning} />
          </div>
        )}
      </AgentSection>

      {/* Architect Output */}
      <AgentSection
        id="architect"
        name="Architect"
        hasOutput={!!architect_output}
        isExpanded={expandedAgents.has("architect")}
        onToggle={() => toggleAgentExpanded("architect")}
      >
        {architect_output && (
          <div className="space-y-3">
            <InfoRow
              label="Architecture"
              value={architect_output.architecture_type}
            />
            <InfoRow
              label="Components"
              value={`${architect_output.components.length} components`}
            />
            <InfoRow
              label="Files"
              value={`${architect_output.file_structure.length} files`}
            />

            {/* Components */}
            <div>
              <h4 className="text-xs font-medium text-foreground-muted mb-2">
                Components
              </h4>
              <div className="space-y-1">
                {architect_output.components.map((comp, i) => (
                  <div
                    key={i}
                    className="text-xs p-2 bg-background-tertiary rounded"
                  >
                    <div className="flex items-center gap-2">
                      <span className="font-medium">{comp.name}</span>
                      <span className="text-foreground-subtle">
                        {comp.type}
                      </span>
                    </div>
                    <p className="mt-1 text-foreground-muted">
                      {comp.description}
                    </p>
                  </div>
                ))}
              </div>
            </div>

            {/* Data Flow */}
            <div>
              <h4 className="text-xs font-medium text-foreground-muted mb-1">
                Data Flow
              </h4>
              <p className="text-xs text-foreground-muted">
                {architect_output.data_flow}
              </p>
            </div>

            <ReasoningBlock text={architect_output.reasoning} />
          </div>
        )}
      </AgentSection>

      {/* Engineer Output */}
      <AgentSection
        id="engineer"
        name="Engineer"
        hasOutput={!!engineer_output}
        isExpanded={expandedAgents.has("engineer")}
        onToggle={() => toggleAgentExpanded("engineer")}
      >
        {engineer_output && (
          <div className="space-y-3">
            <InfoRow
              label="Files Generated"
              value={`${engineer_output.files.length} files`}
            />
            <InfoRow
              label="Dependencies"
              value={
                engineer_output.dependencies_added.length > 0
                  ? engineer_output.dependencies_added.join(", ")
                  : "None"
              }
            />

            {/* Files List */}
            <div>
              <h4 className="text-xs font-medium text-foreground-muted mb-2">
                Generated Files
              </h4>
              <div className="max-h-40 overflow-auto space-y-1">
                {engineer_output.files.map((file, i) => (
                  <div
                    key={i}
                    className="text-xs p-2 bg-background-tertiary rounded flex items-center gap-2"
                  >
                    <span className="font-mono">{file.file_path}</span>
                    <span className="text-foreground-subtle">
                      ({file.file_language})
                    </span>
                  </div>
                ))}
              </div>
            </div>

            {/* Setup Instructions */}
            {engineer_output.setup_instructions.length > 0 && (
              <div>
                <h4 className="text-xs font-medium text-foreground-muted mb-1">
                  Setup Instructions
                </h4>
                <ol className="text-xs text-foreground-muted list-decimal list-inside space-y-1">
                  {engineer_output.setup_instructions.map((step, i) => (
                    <li key={i}>{step}</li>
                  ))}
                </ol>
              </div>
            )}

            <ReasoningBlock text={engineer_output.reasoning} />
          </div>
        )}
      </AgentSection>

      {/* QA Output */}
      <AgentSection
        id="qa"
        name="QA"
        hasOutput={!!qa_output}
        isExpanded={expandedAgents.has("qa")}
        onToggle={() => toggleAgentExpanded("qa")}
      >
        {qa_output && (
          <div className="space-y-3">
            {/* Quality Score */}
            <div className="flex items-center gap-4">
              <div className="flex-1">
                <div className="flex justify-between text-xs mb-1">
                  <span className="text-foreground-muted">Quality Score</span>
                  <span className="font-medium">
                    {qa_output.quality_score}/100
                  </span>
                </div>
                <div className="h-2 bg-background-tertiary rounded-full overflow-hidden">
                  <div
                    className={cn(
                      "h-full transition-all",
                      qa_output.quality_score >= 80
                        ? "bg-success"
                        : qa_output.quality_score >= 60
                        ? "bg-warning"
                        : "bg-error",
                    )}
                    style={{ width: `${qa_output.quality_score}%` }}
                  />
                </div>
              </div>
              <ApprovalBadge status={qa_output.approval_status} />
            </div>

            <InfoRow
              label="Test Coverage"
              value={qa_output.test_coverage_estimate}
            />
            <InfoRow
              label="Test Cases"
              value={`${qa_output.test_cases.length} tests`}
            />

            {/* Validation Notes */}
            {qa_output.validation_notes.length > 0 && (
              <div>
                <h4 className="text-xs font-medium text-foreground-muted mb-2">
                  Validation Notes
                </h4>
                <div className="space-y-1">
                  {qa_output.validation_notes.slice(0, 5).map((note, i) => (
                    <div
                      key={i}
                      className="text-xs p-2 bg-background-tertiary rounded flex items-start gap-2"
                    >
                      <SeverityIcon severity={note.severity} />
                      <div>
                        <p>{note.description}</p>
                        <p className="text-foreground-subtle mt-1">
                          {note.recommendation}
                        </p>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Code Review Summary */}
            <div>
              <h4 className="text-xs font-medium text-foreground-muted mb-1">
                Code Review Summary
              </h4>
              <p className="text-xs text-foreground-muted">
                {qa_output.code_review_summary}
              </p>
            </div>

            <ReasoningBlock text={qa_output.reasoning} />
          </div>
        )}
      </AgentSection>
    </div>
  );
}

// Helper Components

interface AgentSectionProps {
  id: string;
  name: string;
  hasOutput: boolean;
  isExpanded: boolean;
  onToggle: () => void;
  children: React.ReactNode;
}

function AgentSection({
  id,
  name,
  hasOutput,
  isExpanded,
  onToggle,
  children,
}: AgentSectionProps) {
  return (
    <div
      className={cn(
        "rounded-lg border border-border overflow-hidden",
        getAgentBgColor(id),
      )}
    >
      <button
        onClick={onToggle}
        className="w-full px-3 py-2 flex items-center justify-between hover:bg-background-tertiary/50 transition-colors"
      >
        <div className="flex items-center gap-2">
          {isExpanded ? (
            <ChevronDown className="h-4 w-4 text-foreground-muted" />
          ) : (
            <ChevronRight className="h-4 w-4 text-foreground-muted" />
          )}
          <span className={cn("font-medium text-sm", getAgentColor(id))}>
            {name} Agent
          </span>
        </div>
        {hasOutput ? (
          <CheckCircle className="h-4 w-4 text-success" />
        ) : (
          <span className="text-xs text-foreground-subtle">Pending</span>
        )}
      </button>
      {isExpanded && hasOutput && <div className="px-3 pb-3">{children}</div>}
    </div>
  );
}

function InfoRow({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex justify-between text-xs">
      <span className="text-foreground-muted">{label}</span>
      <span className="font-medium">{value}</span>
    </div>
  );
}

function ReasoningBlock({ text }: { text: string }) {
  const [expanded, setExpanded] = useState(false);

  return (
    <div>
      <button
        onClick={() => setExpanded(!expanded)}
        className="text-xs text-foreground-subtle hover:text-foreground flex items-center gap-1"
      >
        {expanded ? (
          <ChevronDown className="h-3 w-3" />
        ) : (
          <ChevronRight className="h-3 w-3" />
        )}
        Show reasoning
      </button>
      {expanded && (
        <p className="mt-2 text-xs text-foreground-muted bg-background-tertiary p-2 rounded">
          {text}
        </p>
      )}
    </div>
  );
}

function ApprovalBadge({ status }: { status: string }) {
  const statusConfig: Record<
    string,
    { color: string; icon: typeof CheckCircle }
  > = {
    approved: { color: "text-success bg-success/10", icon: CheckCircle },
    "needs-revision": {
      color: "text-warning bg-warning/10",
      icon: AlertTriangle,
    },
    rejected: { color: "text-error bg-error/10", icon: AlertCircle },
  };

  const config = statusConfig[status] || statusConfig["needs-revision"];
  const Icon = config.icon;

  return (
    <div
      className={cn(
        "flex items-center gap-1 px-2 py-1 rounded text-xs font-medium",
        config.color,
      )}
    >
      <Icon className="h-3 w-3" />
      {status}
    </div>
  );
}

function SeverityIcon({ severity }: { severity: string }) {
  const icons: Record<string, typeof AlertCircle> = {
    error: AlertCircle,
    warning: AlertTriangle,
    info: Info,
  };

  const Icon = icons[severity.toLowerCase()] || Info;

  return (
    <Icon className={cn("h-4 w-4 shrink-0", getSeverityColor(severity))} />
  );
}
