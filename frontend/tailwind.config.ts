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
        // Dark theme inspired by Cursor/Lovable
        background: {
          DEFAULT: "#0a0a0b",
          secondary: "#111113",
          tertiary: "#18181b",
        },
        foreground: {
          DEFAULT: "#fafafa",
          muted: "#a1a1aa",
          subtle: "#71717a",
        },
        border: {
          DEFAULT: "#27272a",
          muted: "#1f1f23",
        },
        accent: {
          DEFAULT: "#8b5cf6",
          hover: "#7c3aed",
          muted: "#6d28d9",
        },
        success: {
          DEFAULT: "#22c55e",
          muted: "#16a34a",
        },
        warning: {
          DEFAULT: "#f59e0b",
          muted: "#d97706",
        },
        error: {
          DEFAULT: "#ef4444",
          muted: "#dc2626",
        },
      },
      fontFamily: {
        sans: ["Inter", "system-ui", "sans-serif"],
        mono: ["JetBrains Mono", "Fira Code", "monospace"],
      },
      animation: {
        "pulse-slow": "pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite",
        "fade-in": "fadeIn 0.3s ease-in-out",
        "slide-up": "slideUp 0.3s ease-out",
      },
      keyframes: {
        fadeIn: {
          "0%": { opacity: "0" },
          "100%": { opacity: "1" },
        },
        slideUp: {
          "0%": { opacity: "0", transform: "translateY(10px)" },
          "100%": { opacity: "1", transform: "translateY(0)" },
        },
      },
    },
  },
  plugins: [],
};

export default config;
