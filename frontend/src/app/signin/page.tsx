"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { LogIn, Eye, EyeOff } from "lucide-react";
import { useAuthStore } from "@/lib/authStore";

export default function SignInPage() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const router = useRouter();

  const { signin, isLoading, error, setError, user, token, initialize } =
    useAuthStore();

  useEffect(() => {
    initialize();
  }, [initialize]);

  useEffect(() => {
    if (token && user) {
      router.replace("/");
    }
  }, [token, user, router]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!email.trim() || !password.trim()) return;

    const success = await signin(email.trim(), password);
    if (success) {
      router.push("/");
    }
  };

  return (
    <main className="min-h-screen flex flex-col items-center justify-center px-6 relative">
      {/* Background glow */}
      <div
        className="pointer-events-none fixed inset-0 z-0"
        aria-hidden="true"
        style={{
          background:
            "radial-gradient(ellipse 80% 50% at 50% -20%, rgba(255,255,255,0.03) 0%, transparent 60%)",
        }}
      />

      <div className="relative z-10 w-full max-w-sm">
        {/* Logo */}
        <div className="text-center mb-8">
          <a href="/" className="inline-block">
            <span className="font-semibold text-2xl tracking-tight">
              MetaGPT
            </span>
          </a>
          <p className="mt-2 text-sm text-foreground-muted">
            Sign in to your account
          </p>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit} className="space-y-4">
          {error && (
            <div className="rounded-lg border border-red-500/30 bg-red-500/10 px-4 py-3 text-sm text-red-400">
              {error}
            </div>
          )}

          <div>
            <label
              htmlFor="email"
              className="block text-sm font-medium text-foreground-muted mb-1.5"
            >
              Email
            </label>
            <input
              id="email"
              type="email"
              value={email}
              onChange={(e) => {
                setEmail(e.target.value);
                if (error) setError(null);
              }}
              placeholder="you@example.com"
              required
              className="w-full rounded-lg border border-border bg-background-secondary px-3.5 py-2.5 text-sm text-foreground placeholder:text-foreground-subtle focus:outline-none focus:ring-1 focus:ring-foreground/30 transition-colors"
            />
          </div>

          <div>
            <label
              htmlFor="password"
              className="block text-sm font-medium text-foreground-muted mb-1.5"
            >
              Password
            </label>
            <div className="relative">
              <input
                id="password"
                type={showPassword ? "text" : "password"}
                value={password}
                onChange={(e) => {
                  setPassword(e.target.value);
                  if (error) setError(null);
                }}
                placeholder="Your password"
                required
                className="w-full rounded-lg border border-border bg-background-secondary px-3.5 py-2.5 pr-10 text-sm text-foreground placeholder:text-foreground-subtle focus:outline-none focus:ring-1 focus:ring-foreground/30 transition-colors"
              />
              <button
                type="button"
                onClick={() => setShowPassword(!showPassword)}
                className="absolute right-3 top-1/2 -translate-y-1/2 text-foreground-subtle hover:text-foreground-muted transition-colors"
              >
                {showPassword ? (
                  <EyeOff className="h-4 w-4" />
                ) : (
                  <Eye className="h-4 w-4" />
                )}
              </button>
            </div>
          </div>

          <button
            type="submit"
            disabled={isLoading || !email.trim() || !password.trim()}
            className="w-full flex items-center justify-center gap-2 rounded-lg bg-accent px-4 py-2.5 text-sm font-medium text-background transition-all duration-200 hover:bg-accent-hover disabled:pointer-events-none disabled:opacity-40"
          >
            {isLoading ? (
              <>
                <div className="h-4 w-4 border-2 border-background/20 border-t-background rounded-full animate-spin" />
                Signing in...
              </>
            ) : (
              <>
                <LogIn className="h-4 w-4" />
                Sign In
              </>
            )}
          </button>
        </form>

        {/* Sign up link */}
        <p className="mt-6 text-center text-sm text-foreground-muted">
          Don&apos;t have an account?{" "}
          <a
            href="/signup"
            className="text-foreground hover:underline font-medium"
          >
            Sign up
          </a>
        </p>
      </div>
    </main>
  );
}
