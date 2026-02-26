## MetaGPT – Architecture Overview

This document gives a concise, high‑level overview of the MetaGPT architecture.  
For deep implementation details, see `docs/TECHNICAL_OVERVIEW.md`.

---

## 1. System at a Glance

MetaGPT is a **production‑ready agentic code generation system** built around a multi‑stage LLM pipeline:

```text
User (Browser / API client)
    ↓
Frontend (Next.js 14, TypeScript, Tailwind)
    ↓
Backend API (FastAPI, LangChain, LangGraph)
    ↓
Agent Pipeline (Manager → Architect → Engineer → QA)
    ↓
Storage & RAG (projects, artifacts, vector store)
    ↓
Frontend UI (projects list, workspace, files, agent outputs, chat)
```

It consists of:

- **Backend** (`backend/`): FastAPI + LangChain + LangGraph + Gemini 3
- **Frontend** (`frontend/`): Next.js 14 (App Router) + TypeScript + Tailwind CSS

The backend orchestrates multi‑step LLM agents that design and generate codebases. The frontend lets users submit prompts, inspect pipeline progress, browse generated files, and iterate via chat.

---

## 2. High‑Level Flow

1. **User submits prompt**
  - From the web UI or via `POST /api/v1/pipeline/run` or `/stream`.
  - Optional auth flows (signin/signup) run via the frontend and backend `auth` layer.
2. **Backend initializes a project & pipeline**
  - Creates a new project entry and a pipeline run.
  - Sets up initial pipeline state (prompt, config, IDs).
3. **LangGraph orchestrates agents**
  - **Manager**: turns the prompt into structured requirements.
  - **Architect**: designs architecture and file structure.
  - **Engineer**: generates concrete code and configuration files.
  - **QA**: validates artifacts, writes tests, and provides feedback.
  - Agents can optionally call into RAG (`app/rag/`) to ground reasoning in existing project artifacts.
4. **Artifacts are stored**
  - Source files, project tree, and reasoning logs are written under a per‑project directory via `storage/`.
5. **Frontend visualizes the result**
  - Users see pipeline progress, agent outputs, file tree, code, and (when enabled) a live React preview.
6. **User iterates via chat**
  - Chat messages go through `/api/v1/chat/{id}`, are stored by `chat_service`, and can trigger further pipeline activity.
  - The UI and pipeline timeline update in real time as new events arrive.

---

## 3. Backend Architecture

**Tech stack**

- Python 3.11+
- FastAPI for HTTP APIs
- LangChain + LangGraph for agent orchestration
- Google Gemini 3 (via Google Generative AI) for LLM calls

**Key modules (`backend/app/`)**

- `main.py` – FastAPI application entry point.
- `config.py` – Central application settings (LLM, projects dir, debug flags, etc.).
- `db.py` / `auth.py` – Database/session setup and authentication helpers.
- `api/` – Versioned API endpoints (`/api/v1/...`) for projects, pipeline, files, chat, auth, and RAG.
- `agents/` – Manager, Architect, Engineer, and QA implementations built on a shared base class.
- `graph/` – LangGraph definitions (pipeline state model and agent graph).
- `llm/` – Central Gemini configuration and helpers.
- `models/` – Persistence/domain models for projects and users.
- `schemas/` – Pydantic models for requests, responses, and typed agent outputs.
- `sop/` – Standard Operating Procedures (detailed instructions) for each agent.
- `services/` – Business logic (pipeline orchestration, chat, sandboxing).
- `storage/` – File & project storage, rooted at `PROJECTS_DIR`.
- `rag/` – Retrieval‑augmented generation utilities (embeddings, vector store, indexer, retriever).

**Configuration**

- `.env` in `backend/` with:
  - `GOOGLE_API_KEY` (required)
  - `LLM_MODEL`, `LLM_TEMPERATURE`, `LLM_MAX_TOKENS`
  - `PROJECTS_DIR`, `DEBUG`, etc.
- `app/config.py` centralizes configuration access.

---

## 4. Frontend Architecture

**Tech stack**

- Next.js 14 (App Router)
- TypeScript
- Tailwind CSS

**Key modules (`frontend/src/`)**

- `app/`
  - `page.tsx` – Landing page and entry point.
  - `projects/page.tsx` – Projects list.
  - `project/[id]/page.tsx` – Project workspace (file explorer, code viewer, outputs, chat).
  - `signin/page.tsx`, `signup/page.tsx` – Auth flows (if enabled).
  - `layout.tsx` – Global layout, theme, and providers.
- `components/`
  - `AgentOutputs.tsx` – Visualizes outputs per agent stage.
  - `ChatPanel.tsx` – Chat interface tied to backend chat endpoints.
  - `ExecutionTimeline.tsx` – Pipeline progress and state.
  - `FileExplorer.tsx` – Project file tree.
  - `CodeViewer.tsx` – Syntax‑highlighted file viewer.
  - `PreviewPanel.tsx` + `PreviewFrame.tsx` – Live preview for React projects (when enabled).
  - Additional UI elements (icons, effects, cards) for polished UX.
- `lib/`
  - `api.ts` – Typed API client using `NEXT_PUBLIC_API_URL`.
  - `store.ts` – Main Zustand store for project, file, and pipeline state.
  - `authStore.ts` – Zustand store for authentication state.
  - `utils.ts`, `editorThemes.ts` – UI and editor helpers.

**Styling & configuration**

- `app/globals.css` – Global styles configured with Tailwind.
- `tailwind.config.ts` – Design tokens and dark theme configuration.
- `middleware.ts` – Next.js middleware for auth/routing concerns.

---

## 5. API Surface (Top‑Level)

The backend exposes a small, focused set of HTTP APIs:

- **Projects**
  - `POST /api/v1/projects` – Create a project.
  - `GET /api/v1/projects` – List projects.
  - `GET /api/v1/projects/{id}` – Project details.
  - `GET /api/v1/projects/{id}/reasoning` – Aggregated reasoning across agents.
- **Pipeline**
  - `POST /api/v1/pipeline/run` – Run pipeline in one shot.
  - `POST /api/v1/pipeline/stream` – Run pipeline with streaming updates.
  - `GET /api/v1/pipeline/{id}/status` – Current pipeline status.
  - `GET /api/v1/pipeline/{id}/artifacts` – Generated artifacts metadata.
- **Files**
  - `GET /api/v1/files/{id}/tree` – Project file tree.
  - `GET /api/v1/files/{id}/content/{path}` – File content.
  - `PUT /api/v1/files/{id}/content/{path}` – Update file content.
- **Chat**
  - `POST /api/v1/chat/{id}` – Send chat message.
  - `GET /api/v1/chat/{id}/history` – Chat history for a project/pipeline.

The frontend calls these APIs exclusively through `lib/api.ts`, keeping contracts centralized and testable.

---

## 6. Development & Quality

**Backend**

- Dependency management: `uv` + `pyproject.toml`.
- Run server: `uv run serve` (or `uv run uvicorn app.main:app --reload`).
- Tests: `uv run pytest`.
- Type checks: `uv run mypy app`.
- Linting: `uv run ruff check app`.

**Frontend**

- Dependency management: `npm`.
- Dev server: `npm run dev`.
- Production build: `npm run build`.
- Linting: `npm run lint`.
- Type checks: `npm run type-check`.

---

## 7. Where to Go Next

- **New contributors**
  - Start with `README.md` for a quick overview.
  - Read this `ARCHITECTURE.md` to understand how pieces fit together.
  - Use `docs/TECHNICAL_OVERVIEW.md` when you need file‑level detail or are modifying internals.
- **Extending the system**
  - To add a new agent role, see the “Extensibility Guide” in `TECHNICAL_OVERVIEW.md`.
  - To change storage, add endpoints, or evolve the UI, follow the same guide and use the directories listed above as your starting points.

