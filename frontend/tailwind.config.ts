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
        // Monochrome dark theme - black, white, grey
        background: {
          DEFAULT: "#0a0a0a",
          secondary: "#121212",
          tertiary: "#1a1a1a",
        },
        foreground: {
          DEFAULT: "#ffffff",
          muted: "#a0a0a0",
          subtle: "#666666",
        },
        border: {
          DEFAULT: "#2a2a2a",
          muted: "#1e1e1e",
        },
        accent: {
          DEFAULT: "#ffffff",
          hover: "#e0e0e0",
          muted: "#888888",
        },
        success: {
          DEFAULT: "#4ade80",
          muted: "#22c55e",
        },
        warning: {
          DEFAULT: "#fbbf24",
          muted: "#f59e0b",
        },
        error: {
          DEFAULT: "#f87171",
          muted: "#ef4444",
        },
      },
      fontFamily: {
        sans: ["Google Sans", "Google Sans Text", "system-ui", "sans-serif"],
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
