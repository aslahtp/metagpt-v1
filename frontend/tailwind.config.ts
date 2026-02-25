import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  darkMode: "class",
  theme: {
    extend: {
      colors: {
        background: {
          DEFAULT: "rgb(var(--color-background) / <alpha-value>)",
          secondary: "rgb(var(--color-background-secondary) / <alpha-value>)",
          tertiary: "rgb(var(--color-background-tertiary) / <alpha-value>)",
        },
        foreground: {
          DEFAULT: "rgb(var(--color-foreground) / <alpha-value>)",
          muted: "rgb(var(--color-foreground-muted) / <alpha-value>)",
          subtle: "rgb(var(--color-foreground-subtle) / <alpha-value>)",
        },
        border: {
          DEFAULT: "rgb(var(--color-border) / <alpha-value>)",
          muted: "rgb(var(--color-border-muted) / <alpha-value>)",
        },
        accent: {
          DEFAULT: "rgb(var(--color-accent) / <alpha-value>)",
          hover: "rgb(var(--color-accent-hover) / <alpha-value>)",
          muted: "rgb(var(--color-accent-muted) / <alpha-value>)",
        },
        success: {
          DEFAULT: "rgb(var(--color-success) / <alpha-value>)",
          muted: "rgb(var(--color-success-muted) / <alpha-value>)",
        },
        warning: {
          DEFAULT: "rgb(var(--color-warning) / <alpha-value>)",
          muted: "rgb(var(--color-warning-muted) / <alpha-value>)",
        },
        error: {
          DEFAULT: "rgb(var(--color-error) / <alpha-value>)",
          muted: "rgb(var(--color-error-muted) / <alpha-value>)",
        },
      },
      fontFamily: {
        sans: ["Google Sans", "Google Sans Text", "system-ui", "sans-serif"],
        mono: ["JetBrains Mono", "Fira Code", "monospace"],
      },
      animation: {
        "pulse-slow": "pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite",
        "fade-in": "fadeIn 0.5s ease-out forwards",
        "fade-in-up": "fadeInUp 0.6s ease-out forwards",
        "slide-up": "slideUp 0.3s ease-out",
        "message-in":
          "messageIn 0.45s cubic-bezier(0.22, 1, 0.36, 1) forwards",
        "star-movement-bottom":
          "star-movement-bottom linear infinite alternate",
        "star-movement-top": "star-movement-top linear infinite alternate",
        "wave-bar": "wave-bar 1.2s ease-in-out infinite",
        "chat-breathe": "chatBreathe 1.4s cubic-bezier(0.45, 0, 0.55, 1) infinite",
        "dot-pulse":
          "dotPulse 1.2s cubic-bezier(0.4, 0, 0.6, 1) infinite",
      },
      keyframes: {
        fadeIn: {
          "0%": { opacity: "0" },
          "100%": { opacity: "1" },
        },
        fadeInUp: {
          "0%": { opacity: "0", transform: "translateY(16px)" },
          "100%": { opacity: "1", transform: "translateY(0)" },
        },
        messageIn: {
          "0%": {
            opacity: "0",
            transform: "translateY(10px) scale(0.98)",
          },
          "100%": {
            opacity: "1",
            transform: "translateY(0) scale(1)",
          },
        },
        slideUp: {
          "0%": { opacity: "0", transform: "translateY(10px)" },
          "100%": { opacity: "1", transform: "translateY(0)" },
        },
        "star-movement-bottom": {
          "0%": { transform: "translate(0%, 0%)", opacity: "1" },
          "100%": { transform: "translate(-100%, 0%)", opacity: "0" },
        },
        "star-movement-top": {
          "0%": { transform: "translate(0%, 0%)", opacity: "1" },
          "100%": { transform: "translate(100%, 0%)", opacity: "0" },
        },
        "wave-bar": {
          "0%, 60%, 100%": { transform: "scaleY(0.4)" },
          "30%": { transform: "scaleY(1)" },
        },
        chatBreathe: {
          "0%, 100%": { transform: "scaleY(0.5)", opacity: "0.7" },
          "50%": { transform: "scaleY(1)", opacity: "1" },
        },
        dotPulse: {
          "0%, 100%": { transform: "scale(0.5)", opacity: "0.6" },
          "50%": { transform: "scale(1)", opacity: "1" },
        },
      },
    },
  },
  plugins: [],
};

export default config;
