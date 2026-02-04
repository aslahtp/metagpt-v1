"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import {
  Sparkles,
  ArrowRight,
  Code2,
  Layers,
  CheckCircle,
  Zap,
} from "lucide-react";

export default function HomePage() {
  const [prompt, setPrompt] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const router = useRouter();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!prompt.trim() || isLoading) return;

    setIsLoading(true);

    try {
      // Create project and navigate to it
      const response = await fetch("/api/v1/projects", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ prompt: prompt.trim() }),
      });

      if (!response.ok) throw new Error("Failed to create project");

      const project = await response.json();
      router.push(`/project/${project.id}`);
    } catch (error) {
      console.error("Error:", error);
      setIsLoading(false);
    }
  };

  const features = [
    {
      icon: Layers,
      title: "SOP-Driven Agents",
      description:
        "Four specialized agents with defined Standard Operating Procedures",
    },
    {
      icon: Code2,
      title: "Production-Ready Code",
      description:
        "Generate complete, runnable projects with proper architecture",
    },
    {
      icon: CheckCircle,
      title: "Built-in QA",
      description: "Automatic test generation and code quality validation",
    },
    {
      icon: Zap,
      title: "Powered by Gemini",
      description:
        "Uses Google Gemini 3 Flash for fast, intelligent generation",
    },
  ];

  const examplePrompts = [
    "Build a task management app with React and a REST API",
    "Create a blog platform with Next.js and markdown support",
    "Build a real-time chat application with WebSocket support",
    "Create an e-commerce product catalog with search and filters",
  ];

  return (
    <main className="min-h-screen flex flex-col">
      {/* Header */}
      <header className="border-b border-border">
        <div className="max-w-6xl mx-auto px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Sparkles className="h-6 w-6 text-accent" />
            <span className="font-semibold text-lg">MetaGPT-Lovable</span>
          </div>
          <nav className="flex items-center gap-4">
            <a
              href="/docs"
              className="text-foreground-muted hover:text-foreground text-sm"
            >
              Docs
            </a>
            <a
              href="/projects"
              className="text-foreground-muted hover:text-foreground text-sm"
            >
              Projects
            </a>
          </nav>
        </div>
      </header>

      {/* Hero Section */}
      <section className="flex-1 flex flex-col items-center justify-center px-6 py-16">
        <div className="max-w-3xl mx-auto text-center space-y-8">
          <div className="space-y-4">
            <h1 className="text-4xl md:text-5xl font-bold tracking-tight">
              Transform Ideas into
              <span className="text-accent"> Production Code</span>
            </h1>
            <p className="text-xl text-foreground-muted max-w-2xl mx-auto">
              Describe what you want to build. Our AI agents will design,
              implement, and validate your project automatically.
            </p>
          </div>

          {/* Prompt Input */}
          <form onSubmit={handleSubmit} className="w-full max-w-2xl mx-auto">
            <div className="relative">
              <textarea
                value={prompt}
                onChange={(e) => setPrompt(e.target.value)}
                placeholder="Describe the application you want to build..."
                className="w-full h-32 px-4 py-3 rounded-xl border border-border bg-background-secondary text-foreground placeholder:text-foreground-subtle resize-none focus:outline-none focus:ring-2 focus:ring-accent"
                disabled={isLoading}
              />
              <button
                type="submit"
                disabled={!prompt.trim() || isLoading}
                className="absolute bottom-3 right-3 btn-primary flex items-center gap-2"
              >
                {isLoading ? (
                  <>
                    <div className="h-4 w-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                    Creating...
                  </>
                ) : (
                  <>
                    Generate <ArrowRight className="h-4 w-4" />
                  </>
                )}
              </button>
            </div>
          </form>

          {/* Example Prompts */}
          <div className="space-y-3">
            <p className="text-sm text-foreground-subtle">Try an example:</p>
            <div className="flex flex-wrap gap-2 justify-center">
              {examplePrompts.map((example, i) => (
                <button
                  key={i}
                  onClick={() => setPrompt(example)}
                  className="px-3 py-1.5 text-sm rounded-full border border-border hover:border-accent hover:text-accent transition-colors"
                >
                  {example.slice(0, 40)}...
                </button>
              ))}
            </div>
          </div>
        </div>
      </section>

      {/* Features */}
      <section className="border-t border-border py-16 px-6">
        <div className="max-w-5xl mx-auto">
          <h2 className="text-2xl font-semibold text-center mb-12">
            How It Works
          </h2>
          <div className="grid md:grid-cols-4 gap-6">
            {features.map((feature, i) => (
              <div key={i} className="card text-center space-y-3">
                <div className="w-12 h-12 rounded-xl bg-accent/10 flex items-center justify-center mx-auto">
                  <feature.icon className="h-6 w-6 text-accent" />
                </div>
                <h3 className="font-medium">{feature.title}</h3>
                <p className="text-sm text-foreground-muted">
                  {feature.description}
                </p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Agent Pipeline */}
      <section className="border-t border-border py-16 px-6 bg-background-secondary">
        <div className="max-w-4xl mx-auto">
          <h2 className="text-2xl font-semibold text-center mb-12">
            Agent Pipeline
          </h2>
          <div className="flex flex-col md:flex-row items-center justify-between gap-4">
            {[
              { name: "Manager", desc: "Requirements Analysis" },
              { name: "Architect", desc: "System Design" },
              { name: "Engineer", desc: "Code Generation" },
              { name: "QA", desc: "Testing & Validation" },
            ].map((agent, i) => (
              <div key={i} className="flex items-center gap-4">
                <div className="card text-center min-w-[140px]">
                  <div className="font-medium text-accent">{agent.name}</div>
                  <div className="text-xs text-foreground-muted mt-1">
                    {agent.desc}
                  </div>
                </div>
                {i < 3 && (
                  <ArrowRight className="h-5 w-5 text-foreground-subtle hidden md:block" />
                )}
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-border py-6 px-6">
        <div className="max-w-6xl mx-auto flex items-center justify-between text-sm text-foreground-muted">
          <span>MetaGPT-Lovable</span>
          <span>Powered by Gemini 3 Flash</span>
        </div>
      </footer>
    </main>
  );
}
