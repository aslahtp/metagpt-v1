# ForgeX Frontend

Next.js frontend for the ForgeX agentic system.

## Quick Start

```bash
# Install dependencies
npm install

# Copy environment file
cp .env.example .env.local

# Run development server
npm run dev

# Open http://localhost:3000
```

## Project Structure

```
src/
├── app/                     # Next.js App Router pages & layouts
│   ├── layout.tsx           # Root layout, providers, and theme
│   ├── page.tsx             # Landing page
│   ├── projects/page.tsx    # Projects list
│   ├── project/[id]/page.tsx# Project workspace
│   ├── signin/page.tsx      # Sign-in page
│   └── signup/page.tsx      # Sign-up page
├── components/              # React components
│   ├── AgentOutputs.tsx     # Agent output viewer
│   ├── ChatPanel.tsx        # Chat interface
│   ├── CodeViewer.tsx       # Syntax-highlighted code
│   ├── ExecutionTimeline.tsx# Pipeline progress
│   ├── FileExplorer.tsx     # File tree
│   ├── PreviewPanel.tsx     # React preview
│   └── PreviewFrame.tsx     # Iframe wrapper for preview
├── lib/                     # Utilities & state
│   ├── api.ts               # API client
│   ├── store.ts             # Main Zustand state
│   ├── authStore.ts         # Auth-related Zustand state
│   ├── editorThemes.ts      # Editor/theme helpers
│   └── utils.ts             # Helper functions
├── app/globals.css          # Global Tailwind styles
├── middleware.ts            # Next.js middleware (auth/routing)
└── types/monaco-editor-react.d.ts # Monaco editor type declarations
```

## Features

- Dark theme by default (Cursor/Lovable inspired)
- Real-time pipeline execution timeline
- File explorer with syntax highlighting
- Chat-based project iterations
- React/Next.js project detection

## Scripts

```bash
npm run dev      # Start development server
npm run build    # Build for production
npm run start    # Start production server
npm run lint     # Run ESLint
npm run type-check  # Run TypeScript check
```

## Environment Variables

```bash
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_ENABLE_PREVIEW=true
```
