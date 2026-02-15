"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import {
  ArrowRight,
  Code2,
  Layers,
  CheckCircle,
  Zap,
  BookOpen,
} from "lucide-react";
import StarBorder from "@/components/StarBorder";

const features = [
  {
    icon: Layers,
    title: "SOP-Driven Agents",
    description:
      "Four specialized AI agents, each with defined Standard Operating Procedures that mirror real engineering team workflows.",
  },
  {
    icon: Code2,
    title: "Production-Ready Code",
    description:
      "Generate complete, runnable projects with proper architecture, clean separation of concerns, and best practices baked in.",
  },
  {
    icon: CheckCircle,
    title: "Built-in QA",
    description:
      "Automatic test generation, code quality validation, and iterative refinement before any code reaches you.",
  },
  {
    icon: BookOpen,
    title: "Codebase Understanding",
    description:
      "Deep retrieval-augmented generation that indexes your codebase, understands project context, and produces code that fits seamlessly.",
  },
];

const pipeline = [
  { step: "01", name: "Manager", desc: "Requirements Analysis" },
  { step: "02", name: "Architect", desc: "System Design" },
  { step: "03", name: "Engineer", desc: "Code Generation" },
  { step: "04", name: "QA", desc: "Testing & Validation" },
];

const examplePrompts = [
  "Build a task management app with React and a REST API",
  "Create a blog platform with Next.js and markdown support",
  "Build a real-time chat application with WebSocket support",
  "Create an e-commerce product catalog with search and filters",
];

export default function HomePage() {
  const [prompt, setPrompt] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [scrolled, setScrolled] = useState(false);
  const router = useRouter();

  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 50);
    window.addEventListener("scroll", onScroll, { passive: true });
    return () => window.removeEventListener("scroll", onScroll);
  }, []);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!prompt.trim() || isLoading) return;

    setIsLoading(true);

    try {
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

  return (
    <main className="min-h-screen flex flex-col relative bg-[#14120b]">
      {/* Subtle top radial glow */}
      <div
        className="pointer-events-none fixed inset-0 z-0"
        aria-hidden="true"
        style={{
          background:
            "radial-gradient(ellipse 80% 50% at 50% -20%, rgba(255,255,255,0.03) 0%, transparent 60%)",
        }}
      />

      {/* ── Header ── */}
      <div className="sticky top-0 z-50 w-full flex justify-center px-6">
        <header
          className="flex items-center justify-between backdrop-blur-xl border border-transparent transition-[max-width,height,padding,border-radius,margin,background-color,border-color,box-shadow] duration-500 ease-[cubic-bezier(0.25,0.1,0.25,1)]"
          style={{
            maxWidth: scrolled ? "50%" : "80rem",
            width: "100%",
            height: scrolled ? "2.75rem" : "3.5rem",
            paddingLeft: scrolled ? "1.25rem" : "1.5rem",
            paddingRight: scrolled ? "1.25rem" : "1.5rem",
            borderRadius: scrolled ? "9999px" : "0px",
            marginTop: scrolled ? "0.75rem" : "0px",
            backgroundColor: scrolled
              ? "rgba(29,27,21,0.8)"
              : "rgba(20,18,11,0.8)",
            borderColor: scrolled ? "#2a2a2a" : "transparent",
            borderBottomColor: "#2a2a2a",
            boxShadow: scrolled
              ? "0 10px 15px -3px rgba(0,0,0,0.2)"
              : "none",
          }}
        >
          <a href="/" className="flex items-center group">
            <span className="font-semibold text-lg tracking-tight">
              MetaGPT
            </span>
          </a>
          <nav className="flex items-center gap-5 overflow-hidden">
            <a
              href="/docs"
              className="text-foreground-muted hover:text-foreground text-sm transition-all duration-500"
              style={{
                opacity: scrolled ? 0 : 1,
                width: scrolled ? 0 : "auto",
                marginRight: scrolled ? 0 : undefined,
                pointerEvents: scrolled ? "none" : "auto",
              }}
            >
              Docs
            </a>
            <a
              href="/projects"
              className="text-foreground-muted hover:text-foreground text-sm transition-colors duration-200"
            >
              Projects
            </a>
          </nav>
        </header>
      </div>

      {/* ── Hero ── */}
      <section className="relative z-10 flex-1 flex flex-col items-center justify-center px-6 pt-24 pb-20 md:pt-32 md:pb-28">
        <div className="max-w-3xl mx-auto w-full text-center">
          {/* Badge */}
          <div className="opacity-0 animate-fade-in-up stagger-1 mb-8">
            <span className="inline-flex items-center gap-1.5 rounded-full border border-border px-3.5 py-1 text-xs text-foreground-muted">
              <Zap className="h-3 w-3" />
              Powered by Gemini 3 Flash
            </span>
          </div>

          {/* Title */}
          <h1 className="opacity-0 animate-fade-in-up stagger-2 text-4xl sm:text-5xl md:text-6xl font-bold tracking-[-0.04em] leading-[1.08]">
            Transform Ideas into
            <br />
            <span className="text-foreground">Production Code</span>
          </h1>

          {/* Subtitle */}
          <p className="opacity-0 animate-fade-in-up stagger-3 mt-5 text-lg text-foreground-muted max-w-xl mx-auto text-balance leading-relaxed">
            Describe what you want to build. Our AI agents will design,
            implement, and validate your project — automatically.
          </p>

          {/* Prompt Form */}
          <form
            onSubmit={handleSubmit}
            className="opacity-0 animate-fade-in-up stagger-4 mt-10 w-full max-w-2xl mx-auto"
          >
            <StarBorder
              as="div"
              className="w-full rounded-2xl"
              color="rgba(255,255,255,0.5)"
              speed="8s"
              thickness={1}
            >
              <div className="relative rounded-2xl bg-background-secondary">
                <textarea
                  value={prompt}
                  onChange={(e) => setPrompt(e.target.value)}
                  placeholder="Describe the application you want to build..."
                  rows={3}
                  className={`w-full resize-none rounded-2xl bg-transparent px-5 pt-4 text-[15px] text-foreground placeholder:text-foreground-subtle focus:outline-none transition-[padding] duration-300 ${prompt.trim() || isLoading ? "pb-14" : "pb-4"}`}
                  disabled={isLoading}
                />
                <div
                  className={`absolute bottom-3 right-3 transition-all duration-300 ease-out ${prompt.trim() || isLoading ? "opacity-100 translate-y-0" : "opacity-0 translate-y-2 pointer-events-none"}`}
                >
                  <button
                    type="submit"
                    disabled={!prompt.trim() || isLoading}
                    className="inline-flex items-center gap-2 rounded-xl bg-white px-4 py-2 text-sm font-medium text-black transition-all duration-200 hover:bg-gray-200 disabled:pointer-events-none disabled:opacity-40"
                  >
                    {isLoading ? (
                      <>
                        <div className="h-3.5 w-3.5 border-2 border-black/20 border-t-black rounded-full animate-spin" />
                        Creating...
                      </>
                    ) : (
                      <>
                        Generate
                        <ArrowRight className="h-3.5 w-3.5" />
                      </>
                    )}
                  </button>
                </div>
              </div>
            </StarBorder>
          </form>

          {/* Example Prompts */}
          <div className="opacity-0 animate-fade-in-up stagger-5 mt-6">
            <p className="text-xs text-foreground-subtle mb-3">
              Try an example
            </p>
            <div className="flex flex-wrap gap-2 justify-center">
              {examplePrompts.map((example, i) => (
                <button
                  key={i}
                  onClick={() => setPrompt(example)}
                  className="px-3 py-1.5 text-[13px] text-foreground-muted rounded-lg border border-border hover:bg-background-tertiary hover:text-foreground transition-colors duration-200"
                >
                  {example.length > 44 ? example.slice(0, 44) + "..." : example}
                </button>
              ))}
            </div>
          </div>
        </div>
      </section>

      {/* ── Features ── */}
      <section className="relative z-10 border-t border-border px-6 py-24 md:py-28">
        <div className="max-w-5xl mx-auto">
          <div className="text-center mb-14">
            <p className="text-xs font-medium uppercase tracking-widest text-foreground-subtle mb-3">
              How It Works
            </p>
            <h2 className="text-2xl md:text-3xl font-semibold tracking-tight">
              A complete engineering team, automated
            </h2>
          </div>

          <div className="grid sm:grid-cols-2 gap-4">
            {features.map((feature, i) => (
              <div
                key={i}
                className="group rounded-2xl border border-border bg-background-secondary p-6 space-y-4 transition-colors duration-300 hover:border-foreground-subtle hover:bg-background-secondary/80"
              >
                <div className="w-10 h-10 rounded-lg bg-background-tertiary flex items-center justify-center">
                  <feature.icon className="h-5 w-5 text-foreground-muted" />
                </div>
                <h3 className="font-medium text-[15px]">{feature.title}</h3>
                <p className="text-sm text-foreground-muted leading-relaxed">
                  {feature.description}
                </p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── Agent Pipeline ── */}
      <section className="relative z-10 border-t border-border px-6 py-24 md:py-28">
        <div className="max-w-5xl mx-auto">
          <div className="text-center mb-14">
            <p className="text-xs font-medium uppercase tracking-widest text-foreground-subtle mb-3">
              The Pipeline
            </p>
            <h2 className="text-2xl md:text-3xl font-semibold tracking-tight">
              From prompt to production in four steps
            </h2>
          </div>

          {/* Desktop pipeline */}
          <div className="hidden md:block">
            <div className="grid grid-cols-4 gap-0">
              {pipeline.map((agent, i) => (
                <div key={i} className="relative flex flex-col items-center">
                  {/* Connector line */}
                  {i < pipeline.length - 1 && (
                    <div className="absolute top-[18px] left-[calc(50%+20px)] right-[calc(-50%+20px)] border-t border-border" />
                  )}
                  {/* Step number dot */}
                  <div className="relative z-10 w-9 h-9 rounded-full border border-border bg-[#14120b] flex items-center justify-center mb-4">
                    <span className="text-xs font-mono text-foreground-subtle">
                      {agent.step}
                    </span>
                  </div>
                  <h3 className="font-medium text-[15px] mb-1">{agent.name}</h3>
                  <p className="text-sm text-foreground-muted">{agent.desc}</p>
                </div>
              ))}
            </div>
          </div>

          {/* Mobile pipeline */}
          <div className="md:hidden space-y-0">
            {pipeline.map((agent, i) => (
              <div key={i} className="flex items-start gap-4">
                {/* Vertical track */}
                <div className="flex flex-col items-center">
                  <div className="w-9 h-9 rounded-full border border-border bg-[#14120b] flex items-center justify-center shrink-0">
                    <span className="text-xs font-mono text-foreground-subtle">
                      {agent.step}
                    </span>
                  </div>
                  {i < pipeline.length - 1 && (
                    <div className="w-px flex-1 bg-border my-1 min-h-[32px]" />
                  )}
                </div>
                <div className="pt-1.5 pb-6">
                  <h3 className="font-medium text-[15px] mb-0.5">
                    {agent.name}
                  </h3>
                  <p className="text-sm text-foreground-muted">{agent.desc}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── Footer ── */}
      <footer className="relative z-10 border-t border-border px-6 py-6">
        <div className="max-w-5xl mx-auto flex items-center justify-between text-xs text-foreground-subtle">
          <span>&copy; {new Date().getFullYear()} MetaGPT</span>
          <div className="flex items-center gap-4">
            <a
              href="/docs"
              className="hover:text-foreground-muted transition-colors duration-200"
            >
              Docs
            </a>
            <a
              href="/projects"
              className="hover:text-foreground-muted transition-colors duration-200"
            >
              Projects
            </a>
          </div>
        </div>
      </footer>
    </main>
  );
}
