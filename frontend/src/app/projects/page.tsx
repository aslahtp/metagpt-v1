"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import {
  Sparkles,
  Plus,
  Clock,
  CheckCircle,
  XCircle,
  Loader2,
} from "lucide-react";
import { formatDate, cn } from "@/lib/utils";
import type { Project } from "@/lib/api";

export default function ProjectsPage() {
  const [projects, setProjects] = useState<Project[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function fetchProjects() {
      try {
        const res = await fetch("/api/v1/projects");
        if (res.ok) {
          const data = await res.json();
          setProjects(data);
        }
      } catch (err) {
        console.error("Failed to fetch projects:", err);
      } finally {
        setLoading(false);
      }
    }

    fetchProjects();
  }, []);

  const getStatusIcon = (stage: string) => {
    switch (stage) {
      case "completed":
        return <CheckCircle className="h-4 w-4 text-success" />;
      case "error":
        return <XCircle className="h-4 w-4 text-error" />;
      case "pending":
        return <Clock className="h-4 w-4 text-foreground-subtle" />;
      default:
        return <Loader2 className="h-4 w-4 text-accent animate-spin" />;
    }
  };

  return (
    <main className="min-h-screen">
      {/* Header */}
      <header className="border-b border-border">
        <div className="max-w-6xl mx-auto px-6 py-4 flex items-center justify-between">
          <Link href="/" className="flex items-center gap-2">
            <Sparkles className="h-6 w-6 text-accent" />
            <span className="font-semibold text-lg">MetaGPT</span>
          </Link>
          <Link href="/" className="btn-primary flex items-center gap-2">
            <Plus className="h-4 w-4" />
            New Project
          </Link>
        </div>
      </header>

      {/* Content */}
      <div className="max-w-6xl mx-auto px-6 py-8">
        <h1 className="text-2xl font-bold mb-6">Your Projects</h1>

        {loading ? (
          <div className="flex items-center justify-center py-16">
            <Loader2 className="h-6 w-6 text-accent animate-spin" />
          </div>
        ) : projects.length === 0 ? (
          <div className="text-center py-16">
            <div className="w-16 h-16 rounded-xl bg-accent/10 flex items-center justify-center mx-auto mb-4">
              <Sparkles className="h-8 w-8 text-accent" />
            </div>
            <h2 className="text-xl font-medium mb-2">No projects yet</h2>
            <p className="text-foreground-muted mb-6">
              Create your first project by describing what you want to build.
            </p>
            <Link href="/" className="btn-primary">
              Create Project
            </Link>
          </div>
        ) : (
          <div className="grid gap-4">
            {projects.map((project) => (
              <Link
                key={project.id}
                href={`/project/${project.id}`}
                className="card hover:border-accent/50 transition-colors group"
              >
                <div className="flex items-start justify-between">
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-1">
                      {getStatusIcon(
                        project.state.pipeline_status?.stage || "pending",
                      )}
                      <h3 className="font-medium group-hover:text-accent transition-colors">
                        {project.name || "Untitled Project"}
                      </h3>
                    </div>
                    <p className="text-sm text-foreground-muted line-clamp-2">
                      {project.prompt}
                    </p>
                    <div className="flex items-center gap-4 mt-3 text-xs text-foreground-subtle">
                      <span>ID: {project.id}</span>
                      <span>Created: {formatDate(project.created_at)}</span>
                      {project.state.engineer_output && (
                        <span>
                          {project.state.engineer_output.files.length} files
                        </span>
                      )}
                    </div>
                  </div>
                  <div className="ml-4">
                    <span
                      className={cn(
                        "text-xs px-2 py-1 rounded",
                        project.state.pipeline_status?.stage === "completed"
                          ? "bg-success/10 text-success"
                          : project.state.pipeline_status?.stage === "error"
                          ? "bg-error/10 text-error"
                          : "bg-foreground-subtle/10 text-foreground-subtle",
                      )}
                    >
                      {project.state.pipeline_status?.stage || "pending"}
                    </span>
                  </div>
                </div>
              </Link>
            ))}
          </div>
        )}
      </div>
    </main>
  );
}
