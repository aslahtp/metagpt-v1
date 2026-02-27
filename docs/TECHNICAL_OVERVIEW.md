## MetaGPT – Technical Architecture & Internals

This document provides a detailed, implementation‑oriented overview of the MetaGPT project. It is intended for engineers who want to:

- Understand how all parts of the system fit together
- Navigate the codebase efficiently
- Extend or modify agents, APIs, and UI
- Diagnose issues across backend and frontend boundaries

The project consists of two primary applications:

- **Backend** (`backend/`): FastAPI + LangChain + LangGraph + Gemini Model
- **Frontend** (`frontend/`): Next.js 14 (App Router) + TypeScript + Tailwind CSS

---

## 1. End‑to‑End System Overview

### 1.1 High‑Level Flow

Conceptually, the system implements an **agentic code‑generation pipeline**:

```text
User (Web UI or API client)
    ↓
FastAPI Backend
    ↓
LangGraph Orchestrator
    ↓
SOP‑Driven Agents (Manager → Architect → Engineer → QA)
    ↓
File & Project Storage
    ↓
Frontend visualization (projects list, workspace, files, agent outputs, chat)
```

At a slightly more concrete level:

1. **User submits a prompt** from the frontend or via `POST /api/v1/pipeline/run` / `/stream`.
2. **Backend creates or loads a project**, initializes pipeline state, and triggers a LangGraph workflow.
3. **Agents run in sequence** (or graph‑defined order), each transforming the shared pipeline state:
  - `Manager` turns the raw prompt into requirements.
  - `Architect` designs the system and file structure.
  - `Engineer` generates concrete code artifacts.
  - `QA` validates, writes tests, and suggests improvements.
4. **Artifacts and reasoning are persisted** in `app/storage/` (project directory tree, code files, logs, agent outputs).
5. **Frontend reads and visualizes**:
  - Project metadata and status
  - Agent reasoning and timeline
  - File tree and file contents
  - Chat iterations and history
6. **User iterates** by sending chat messages that feed back into the pipeline to refine the project.

---

## 2. Repository Layout

At the top level:

```text
metagpt-v1/
├── backend/            # FastAPI + LangChain + LangGraph backend
├── frontend/           # Next.js 14 frontend
├── docs/               # Project documentation (this file, examples, walkthroughs)
└── README.md           # High-level landing document
```

This document is the authoritative technical guide to how each folder works in practice.

---

## 3. Backend Architecture (`backend/`)

The backend is a **FastAPI application** that exposes REST endpoints and orchestrates the multi‑agent pipeline via **LangGraph** and **LangChain**, backed by **Google Gemini 3** via the Google Generative AI integration.

### 3.1 Backend Structure

```text
backend/
└── app/
    ├── main.py          # FastAPI application entry point
    ├── config.py        # Application settings (LLM, DB, projects dir, etc.)
    ├── db.py            # Database/session setup (if enabled)
    ├── auth.py          # Authentication helpers and dependencies
    ├── api/             # FastAPI routing layer
    │   ├── router.py    # Top-level API router (mounts versioned endpoints)
    │   └── endpoints/
    │       ├── projects.py  # /api/v1/projects
    │       ├── pipeline.py  # /api/v1/pipeline/*
    │       ├── files.py     # /api/v1/files/*
    │       ├── chat.py      # /api/v1/chat/*
    │       ├── auth.py      # /api/v1/auth/*
    │       └── rag.py       # /api/v1/rag/* (retrieval-augmented features)
    ├── agents/          # SOP-driven agent implementations
    │   ├── base.py      # Base agent class
    │   ├── manager.py   # Manager Agent
    │   ├── architect.py # Architect Agent
    │   ├── engineer.py  # Engineer Agent
    │   └── qa.py        # QA Agent
    ├── graph/           # LangGraph orchestration
    │   ├── state.py     # Pipeline state definition
    │   └── orchestrator.py  # Agent pipeline graph
    ├── llm/             # LLM configuration
    │   └── gemini.py    # Centralized Gemini 3 configuration
    ├── models/          # ORM / domain models
    │   ├── project.py   # Project persistence model
    │   └── user.py      # User/auth persistence model
    ├── schemas/         # Pydantic models (API + agents)
    │   ├── projects.py  # Project request/response schemas
    │   ├── files.py     # File tree & content schemas
    │   └── agents.py    # Agent input/output schemas
    ├── services/        # Business logic layer
    │   ├── chat_service.py      # Chat message handling
    │   ├── pipeline_service.py  # Pipeline orchestration helpers
    │   └── sandbox_service.py   # Code sandboxing / execution helpers
    ├── storage/         # File and project storage
    │   ├── file_store.py    # File-level IO helpers
    │   └── project_store.py # Project-level storage abstraction
    ├── sop/             # Standard Operating Procedures
    │   └── definitions.py   # SOP definitions for all agents
    └── rag/             # Retrieval-augmented generation utilities
        ├── embeddings.py   # Embedding model setup
        ├── vector_store.py # Vector store abstraction
        ├── indexer.py      # Indexing pipeline for project artifacts
        └── retriever.py    # Retrieval helpers used by agents/API
```

There is also:

- `pyproject.toml`: Dependency and build configuration for the backend.
- `tests/`: Pytest suite with API and service‑level tests.

Each submodule has a clear responsibility and is meant to be extended in isolation.

---

### 3.2 Application Entry Point (`app/main.py`)

**Responsibilities:**

- Construct the FastAPI application instance.
- Attach routers from `app/api/endpoints`.
- Configure middleware (CORS, logging, error handling).
- Expose health endpoints (`/health`).
- Provide OpenAPI / Swagger (`/docs`) and ReDoc (`/redoc`) documentation.

**Key concepts:**

- This file is used as the UVicorn target:
  ```bash
  uv run uvicorn app.main:app --reload
  ```
- It typically imports `create_app()` or directly sets up the `FastAPI` instance.
- All public HTTP APIs used by the frontend and external clients flow through here.

---

### 3.3 API Layer (`app/api/endpoints/`)

**Responsibilities:**

- Define typed HTTP endpoints using FastAPI.
- Convert incoming HTTP requests into **service calls** or **graph invocations**.
- Marshal and validate data using Pydantic models from `app/schemas`.
- Group and mount versioned routes via `app/api/router.py`.

The main endpoint groups (implemented in `app/api/endpoints/*.py`) are:

- **Projects**
  - `POST /api/v1/projects` – Create a new project.
  - `GET /api/v1/projects` – List projects.
  - `GET /api/v1/projects/{id}` – Fetch project metadata.
  - `GET /api/v1/projects/{id}/reasoning` – Fetch agent reasoning logs.
- **Pipeline**
  - `POST /api/v1/pipeline/run` – Run pipeline in a single request.
  - `POST /api/v1/pipeline/stream` – Run pipeline with server‑sent events (SSE).
  - `GET /api/v1/pipeline/{id}/status` – Poll pipeline status.
  - `GET /api/v1/pipeline/{id}/artifacts` – Fetch generated artifacts.
- **Files**
  - `GET /api/v1/files/{id}/tree` – Load project file tree.
  - `GET /api/v1/files/{id}/content/{path}` – Load file content.
  - `PUT /api/v1/files/{id}/content/{path}` – Update file content.
- **Chat**
  - `POST /api/v1/chat/{id}` – Submit a chat message for iteration.
  - `GET /api/v1/chat/{id}/history` – Retrieve conversation history.

**Typical structure of an endpoint module:**

- Pydantic request/response models imported from `app/schemas`.
- Router definitions (`APIRouter`) with path operations.
- Dependency injection for database/storage, services, or pipeline orchestrator.
- Translation of backend exceptions to HTTP error responses.

---

### 3.4 Schemas (`app/schemas/`)

**Responsibilities:**

- Define **Pydantic models** for:
  - Requests coming into endpoints.
  - Responses sent back to clients.
  - Internal typed payloads used by agents and services.

Key modules:

- `schemas/projects.py`
  - Request/response types for project creation, listing, and details (e.g., `ProjectCreateRequest`, `ProjectResponse`).
- `schemas/files.py`
  - Tree and content models for project files (e.g., `FileTreeNode`, `FileContentResponse`).
- `schemas/agents.py`
  - Structured output models for the Manager, Architect, Engineer, and QA agents (e.g., `ManagerOutput`, `ArchitectOutput`, etc.).

**Why this matters:**

- Agents use `get_llm_with_structured_output` with these schemas to enforce **typed LLM outputs**.
- Frontend code can mirror these shapes with TypeScript for a consistent, well‑typed API contract.

---

### 3.5 LLM Configuration (`app/llm/gemini.py`)

**Responsibilities:**

- Provide centralized configuration for **Google Gemini Model** via LangChain.
- Expose helper functions:
  ```python
  from app.llm import get_llm, get_llm_with_structured_output
  ```
  - `get_llm()` – returns a standard chat model instance.
  - `get_llm_with_structured_output(pydantic_model)` – wraps the model for structured JSON output.

**Configuration sources:**

- Environment variables (see root `README.md` and `backend/README.md`):
  - `GOOGLE_API_KEY` – required.
  - `LLM_MODEL` – model name (default: `gemini-2.5-flash`).
  - `LLM_TEMPERATURE`, `LLM_MAX_TOKENS`, etc.
- `app/config.py` – central configuration; environment variables override defaults.

**Extension points:**

- Swap models (e.g., different Gemini versions) by changing `LLM_MODEL`.
- Adjust latency/quality trade‑offs with temperature, max tokens, etc.
- Add wrappers for tools or retrievers if needed in the future.

---

### 3.6 SOPs (`app/sop/`)

**Responsibilities:**

- Define **Standard Operating Procedures (SOPs)** for each agent.
- Capture:
  - Agent **role** and **objective**.
  - Expected **inputs** and **outputs**.
  - **Constraints** and quality rules.
  - Checklists used by QA.

SOP definitions live in `backend/app/sop/definitions.py`.

**Conceptual contents of an SOP definition:**

- Prompt templates: system prompts with detailed instructions.
- Example inputs and outputs.
- Structured output annotations (Pydantic schemas).
- Guard rails (e.g., “do not modify tests unless necessary”).

Agents read from these definitions when constructing their prompts and evaluation logic.

---

### 3.7 Agents (`app/agents/`)

**Responsibilities:**

- Implement the **core behaviors** of each role:
  - `Manager`
  - `Architect`
  - `Engineer`
  - `QA`
- Provide reusable base behavior in `base.py`.

`**base.py`:**

- Likely defines:
  - A common interface (e.g., `run(input_state) -> output_state`).
  - Shared logging and tracing.
  - Access to the configured LLM (`get_llm` / `get_llm_with_structured_output`).
  - Utilities to interact with storage, schemas, and SOPs.

`**manager.py`:**

- Takes the **raw natural language prompt**.
- Produces structured requirements:
  - High‑level features.
  - Non‑functional requirements.
  - Constraints (tech stack, performance, etc.).
  - Edge cases and acceptance criteria.

`**architect.py`:**

- Consumes Manager output.
- Designs the **system architecture and file structure**:
  - Backend APIs, data models, services.
  - Frontend pages, components, state management.
  - External dependencies & integrations.
  - Directory and file layout for the generated project.

`**engineer.py`:**

- Implements the designed architecture as **actual code files**.
- Writes:
  - Backend services/APIs.
  - Frontend components/pages.
  - Configuration, scripts, etc.
- Adheres to style & structure decisions made by the Architect.

`**qa.py`:**

- Reviews artifacts and requirements.
- Produces:
  - Test plans and concrete tests.
  - Bug reports and improvement suggestions.
  - Validation results against SOP checklists.

Each agent is typically a LangChain runnable invoked from the LangGraph graph (see below).

---

### 3.8 Graph Orchestration (`app/graph/`)

**Responsibilities:**

- Define **pipeline state** and transitions.
- Coordinate the order of agents and side‑effects (like file writing).

Key modules:

- `state.py`
  - Defines the **state object** flowing between agents.
  - Likely contains fields like:
    - `prompt`, `project_id`
    - `requirements`, `architecture`, `code_artifacts`, `qa_results`
    - Execution metadata and timestamps.
- `orchestrator.py`
  - Builds a **LangGraph** graph.
  - Connects nodes representing agents and tooling steps.
  - Provides functions to:
    - Start a pipeline run.
    - Stream events (for `/api/v1/pipeline/stream`).
    - Resume or inspect historical runs if supported.

**Data flow:**

1. Initial state created from the pipeline run request.
2. Graph executes:
  - `ManagerNode` → `ArchitectNode` → `EngineerNode` → `QANode` (simplified view).
3. At each step:
  - Agent reads from state and SOPs.
  - Writes results back into state, including artifacts metadata.
4. Storage service persists artifacts (see below).

---

### 3.9 Services (`app/services/`)

**Responsibilities:**

- Contain business logic that is **not** specific to any one framework:
  - Orchestrating pipeline runs on top of LangGraph.
  - Abstracting chat iteration logic and history retrieval.
  - Providing a safe sandbox for executing or analyzing generated code.

Concrete services:

- `pipeline_service.py`
  - Starts and monitors pipeline runs.
  - Bridges between HTTP layer, LangGraph orchestrator, and storage.
- `chat_service.py`
  - Stores and retrieves chat messages tied to a project or pipeline run.
  - May apply transformations or limits (e.g., truncation, summarization) before sending to agents.
- `sandbox_service.py`
  - Provides a controlled environment for running or validating generated code artifacts.
  - Shields the core backend from unsafe execution.

Services are used from:

- API endpoint handlers in `app/api/endpoints/`.
- Graph/agent orchestration code where side‑effects are needed.

---

### 3.10 Storage (`app/storage/`)

**Responsibilities:**

- Persist:
  - Project directory trees.
  - Generated source files.
  - Agent reasoning logs and artifacts.
  - Pipeline run–related metadata.

Key modules:

- `file_store.py`
  - Low‑level helpers for reading/writing individual files.
  - Presents a consistent abstraction over the underlying filesystem.
- `project_store.py`
  - Higher‑level operations on whole projects:
    - Mapping project IDs to directories under `PROJECTS_DIR`.
    - Listing projects and their metadata.
    - Building the file tree structures returned by the files API.

Key concepts:

- `PROJECTS_DIR` environment variable controls the root directory (default `./projects`).
- Project IDs map to subdirectories:
  ```text
  {PROJECTS_DIR}/
    └── {project_id}/
        ├── backend/...
        ├── frontend/...
        ├── artifacts.json
        └── reasoning.log
  ```
- File storage functions are centralized so:
  - Agents and APIs do not directly manipulate raw paths.
  - Switching to a different backend (e.g., S3, database) is easier.

---

### 3.11 Configuration, DB & Auth (`app/config.py`, `app/db.py`, `app/auth.py`)

Configuration is mainly driven by environment variables, loaded and validated by `app/config.py`. Typical keys include:

```bash
GOOGLE_API_KEY=your-api-key
LLM_MODEL=gemini-2.5-flash
LLM_TEMPERATURE=0.7
LLM_MAX_TOKENS=8192
PROJECTS_DIR=./projects
DEBUG=false
```

In local development, `.env.example` in `backend/` is copied to `.env`, and `get_settings()` in `config.py` reads and exposes these settings to the rest of the app (including `llm/gemini.py` and the FastAPI app).

Related modules:

- `db.py`
  - Central place to define database connections or sessions (if a DB is used).
  - Ensures all persistence‑related code shares a single configuration source.
- `auth.py`
  - Houses authentication utilities and FastAPI dependencies (e.g., current user resolution, token verification).
  - Allows endpoints and services to remain agnostic of concrete auth mechanisms.

**Key design principle:** All code that depends on configuration, database, or auth flows through a small number of modules (`config`, `db`, `auth`, `llm` setup, FastAPI app initialization), making it straightforward to reason about runtime behavior in different environments.

---

### 3.12 Testing & Quality (Backend)

From `backend/README.md`:

- **Testing**
  ```bash
  uv run pytest
  uv run pytest --cov=app
  ```
- **Type checking**
  ```bash
  uv run mypy app
  ```
- **Linting**
  ```bash
  uv run ruff check app
  ```

Tests, mypy, and ruff together enforce:

- Correct behavior of endpoints, services, and storage.
- Type correctness, especially important with LLM structured outputs and RAG plumbing.
- Code style and basic static analysis.

---

### 3.13 Models & RAG (`app/models/`, `app/rag/`)

Additional backend modules that are part of the overall architecture:

- `models/`
  - Contains domain/ORM models:
    - `project.py` – representation of projects at the persistence layer.
    - `user.py` – representation of users/auth identities.
  - Keeps persistence concerns (IDs, timestamps, relationships) separate from Pydantic API schemas.
- `rag/`
  - Implements retrieval‑augmented generation (RAG) capabilities:
    - `embeddings.py` – sets up embedding models used for indexing.
    - `vector_store.py` – abstraction over the vector database/backing store.
    - `indexer.py` – pipelines that index project artifacts into the vector store.
    - `retriever.py` – helpers for retrieving context to feed into agents or APIs.
  - Powers RAG‑related endpoints in `api/endpoints/rag.py` and can be used by agents to ground responses in existing project code or documentation.

---

## 4. Frontend Architecture (`frontend/`)

The frontend is a **Next.js 14 App Router** application with:

- TypeScript for type safety.
- Tailwind CSS for styling.
- A dark‑theme UI inspired by Cursor/Lovable.

### 4.1 Frontend Structure

```text
frontend/
└── src/
    ├── app/                 # Next.js App Router pages
    │   ├── page.tsx         # Landing page
    │   ├── project/[id]/    # Project workspace
    │   └── projects/        # Projects list
    ├── components/          # React components
    │   ├── AgentOutputs.tsx # Agent output viewer
    │   ├── ChatPanel.tsx    # Chat interface
    │   ├── CodeViewer.tsx   # Syntax-highlighted code
    │   ├── ExecutionTimeline.tsx  # Pipeline progress
    │   ├── FileExplorer.tsx # File tree
    │   └── PreviewPanel.tsx # React preview
    └── lib/                 # Utilities
        ├── api.ts           # API client
        ├── store.ts         # Zustand state
        └── utils.ts         # Helper functions
```

Other important files:

- `src/app/layout.tsx` – Root layout, theme, and global providers.
- `src/app/globals.css` – Global Tailwind and custom styles.
- `tailwind.config.ts` – Tailwind configuration.
- `middleware.ts` – Next.js middleware (often for auth or routing).
- `types/monaco-editor-react.d.ts` – Type definitions for Monaco integration.

---

### 4.2 Routing & Pages (`src/app/`)

**Key routes:**

- `page.tsx` – Landing page:
  - Explains the product.
  - Likely provides entry point to create a new project.
- `projects/page.tsx` – Projects list:
  - Fetches and displays existing projects from `/api/v1/projects`.
  - Links to individual project workspaces.
- `project/[id]/page.tsx` – Project workspace:
  - The main interactive UI for:
    - Viewing the file tree and code.
    - Inspecting agent outputs and pipeline timeline.
    - Sending chat messages and iterating on the project.
  - Uses multiple shared components from `components/`.
- `signin/page.tsx`, `signup/page.tsx`:
  - Authentication flows if enabled (backed by `lib/authStore.ts` and potentially backend auth endpoints).

**Data fetching pattern:**

- For server components, use `fetch` directly from `/api/v1/...`.
- For client components, rely on `lib/api.ts` (see below).

---

### 4.3 Component Library (`src/components/`)

Some of the major components:

- `AgentOutputs.tsx`
  - Shows the reasoning and outputs from each agent.
  - Likely grouped by role (Manager, Architect, Engineer, QA).
  - May subscribe to streaming updates from the pipeline.
- `ChatPanel.tsx`
  - Chat interface for iterative refinement of projects.
  - Sends messages via `POST /api/v1/chat/{id}`.
  - Renders history via `GET /api/v1/chat/{id}/history`.
- `CodeViewer.tsx`
  - Syntax‑highlighted view for individual files.
  - Powered by a code viewer library (e.g., Monaco or Prism).
  - Reads file content from `GET /api/v1/files/{id}/content/{path}`.
- `ExecutionTimeline.tsx`
  - Visual representation of the pipeline:
    - Manager → Architect → Engineer → QA.
    - Statuses (pending, running, complete, failed).
  - Uses data from pipeline endpoints: status, events, and artifacts.
- `FileExplorer.tsx`
  - Presents a collapsible tree from `/api/v1/files/{id}/tree`.
  - On file click, triggers file content loading for `CodeViewer`.
- `PreviewPanel.tsx`
  - (When enabled) runs a live preview for React projects.
  - Uses `PreviewFrame.tsx` to sandbox the preview.

Other supporting components:

- `MaterialIconWithFallback.tsx`, `SplitText.tsx`, `ShinyText.tsx`, `SpotLightCard.tsx`, `StarBorder.tsx`, etc.:
  - Provide UI polish and animations.
  - Encapsulate icon handling, text effects, cards, and low‑level UI patterns.

There is also an `index.ts` barrel file re‑exporting components for convenience.

---

### 4.4 State Management (`src/lib/store.ts` & `src/lib/authStore.ts`)

The frontend uses **Zustand** for client‑side state.

- `store.ts`:
  - Holds core application state, likely including:
    - Current project metadata.
    - Selected file path.
    - Loaded file contents / current tab.
    - Pipeline execution state and events.
    - UI preferences (e.g., which panels are open).
  - Provides actions for:
    - Fetching/setting projects.
    - Updating pipeline status when new events arrive.
    - Updating file content after an edit.
- `authStore.ts`:
  - Holds authentication state:
    - Current user.
    - Tokens or session flags.
  - Provides helpers for sign‑in/sign‑up flows and logout.

Zustand’s unopinionated nature makes it easy to add or remove slices of state without affecting the rest of the code.

---

### 4.5 API Client (`src/lib/api.ts`)

**Responsibilities:**

- Provide a typed wrapper around `fetch`/`axios` for backend endpoints.
- Centralize the base URL and request configuration.

Key concepts:

- Uses `NEXT_PUBLIC_API_URL` env var:
  ```bash
  NEXT_PUBLIC_API_URL=http://localhost:8000
  ```
- Example operations (conceptual):
  - `getProjects()`
  - `getProject(id)`
  - `runPipeline(payload)`
  - `streamPipeline(payload)` – streaming via EventSource or fetch with `ReadableStream`.
  - `getFileTree(projectId)`
  - `getFileContent(projectId, path)`
  - `updateFileContent(projectId, path, content)`
  - `sendChatMessage(projectId, message)`
  - `getChatHistory(projectId)`

**Advantages of this layer:**

- Keeps backend contracts in one place.
- Simplifies error handling and logging.
- Makes it easier to swap out or mock the backend in tests.

---

### 4.6 Utilities & Styling

- `lib/utils.ts`:
  - Houses small helpers (e.g., class name merging, formatting utilities, type guards).
- `lib/editorThemes.ts`:
  - Theming for Monaco/editor components used in `CodeViewer` or preview.
- `app/globals.css` and `tailwind.config.ts`:
  - Global CSS reset, typography adjustments, dark theme definitions.
  - Tailwind theme extension for consistent spacing, colors, etc.

---

### 4.7 Testing & Quality (Frontend)

Typical quality‑related scripts:

```bash
npm run lint         # ESLint
npm run type-check   # TypeScript checks
npm run build        # Production build (implicitly validates many issues)
```

Combined with backend tooling, this provides a full end‑to‑end quality pipeline.

---

## 5. API & Data Flow Contracts

### 5.1 Frontend ↔ Backend Contracts

The **source of truth** for data structures is `backend/app/schemas/`. Frontend code should mirror these using TypeScript interfaces.

Common patterns:

- **Projects**
  - Response includes:
    - `id`, `name`, and timestamps.
    - Current pipeline status.
    - Possibly links to artifacts and reasoning data.
- **Pipeline**
  - Run request (`/pipeline/run`/`/pipeline/stream`) includes:
    - `prompt` (required).
    - Optional configuration fields (e.g., project name, settings).
  - Status responses include:
    - Current stage (Manager, Architect, etc.).
    - Progress percentages or step index.
    - Error information if the run failed.
- **Files**
  - File tree is a recursive structure of nodes with:
    - `name`, `path`, `type` (`file` or `directory`), and `children`.
  - File content endpoints exchange:
    - `content` as string, and possibly metadata (language, size, etc.).
- **Chat**
  - Messages are:
    - Directional (user vs agent).
    - Time‑stamped.
    - Associated with a project or pipeline run.

---

### 5.2 Pipeline Streaming Semantics

Endpoint: `POST /api/v1/pipeline/stream`

**Behavior:**

- Uses SSE (Server‑Sent Events) or streaming responses.
- Emits events like:
  - `stage_started` / `stage_completed` for each agent.
  - Partial reasoning or token streams.
  - Final artifact summary.

**Frontend handling:**

- `lib/api.ts` likely wraps this in:
  - An `EventSource` or streaming `fetch`.
  - A callback API that pushes events into Zustand store.
- `ExecutionTimeline` and `AgentOutputs` subscribe to updated store values and re‑render.

---

## 6. Operational Concerns

### 6.1 Local Development

- **Backend**
  ```bash
  cd backend
  cp .env.example .env
  # configure GOOGLE_API_KEY and other vars
  uv sync
  uv run serve  # or uv run uvicorn app.main:app --reload
  ```
- **Frontend**
  ```bash
  cd frontend
  npm install
  cp .env.example .env.local
  npm run dev
  ```

### 6.2 Production Deployment (Conceptual)

Not all deployment pieces are included in this repo, but in a typical setup:

- Backend:
  - Containerized FastAPI app (UVicorn + Gunicorn).
  - Environment variables injected by orchestration (Kubernetes, ECS, etc.).
  - HTTPS termination at gateway or reverse proxy.
  - Persistent volume or object storage for `PROJECTS_DIR`.
- Frontend:
  - Built Next.js app (`npm run build`).
  - Deployed as:
    - Static export + Node server, or
    - Edge‑hosted app (Vercel, etc.).

---

## 7. Extensibility Guide

### 7.1 Adding a New Agent

1. **Create SOP entry** in `app/sop/definitions.py`:
  - Define role, objectives, inputs, outputs, constraints, and checklist.
2. **Add a new Pydantic schema** in `app/schemas/agents.py` (or similar).
3. **Implement the agent** in `app/agents/`:
  - Inherit from base agent class.
  - Use `get_llm_with_structured_output` for typed outputs.
4. **Wire into graph** in `app/graph/orchestrator.py`:
  - Add a new node.
  - Extend pipeline state in `state.py`.
  - Insert in appropriate position in graph.
5. **Expose results via API**:
  - Update endpoints and response schemas if new data is user‑visible.
6. **Update frontend**:
  - Extend `AgentOutputs` to show new agent’s output.
  - If necessary, update timeline stages.

---

### 7.2 Changing Project Storage

1. Update storage implementation in `app/storage/`:
  - Replace direct filesystem calls with new backend (e.g., S3, DB).
2. Keep the public storage interface stable:
  - `get_file_tree`, `read_file`, `write_file`, `list_projects`, etc.
3. No changes needed to agents or APIs as long as the storage interface contracts remain the same.

---

### 7.3 Evolving the Frontend UI

- To add a new view or visualization:
  1. Add an endpoint or extend an existing one in `app/api/endpoints/`.
  2. Add a corresponding function in `frontend/src/lib/api.ts`.
  3. Extend Zustand store with new state & actions.
  4. Create a component under `components/` and integrate it into the appropriate page.
- To adjust theme / styling:
  - Make changes in `globals.css` and `tailwind.config.ts`.
  - Keep component styles constrained to Tailwind utility classes for consistency.

---

## 8. Quick Navigation Reference

Use this section when onboarding or exploring the repo:

- **Overall architecture & high‑level docs**
  - `docs/TECHNICAL_OVERVIEW.md` – This document; deep technical tour.
- **Backend**
  - `backend/app/main.py` – FastAPI entry point.
  - `backend/app/api/endpoints/` – All HTTP endpoints.
  - `backend/app/agents/` – Manager, Architect, Engineer, QA.
  - `backend/app/graph/` – LangGraph pipeline orchestration.
  - `backend/app/sop/definitions.py` – Agent SOP definitions.
  - `backend/app/llm/gemini.py` – Gemini 3 configuration.
  - `backend/app/schemas/` – Pydantic models for APIs and agents.
  - `backend/app/services/` – Business logic and integration services.
  - `backend/app/storage/` – Project and artifact persistence.
- **Frontend**
  - `frontend/src/app/` – Next.js routes and layouts.
  - `frontend/src/components/` – Core UI building blocks.
  - `frontend/src/lib/api.ts` – Backend API client.
  - `frontend/src/lib/store.ts` – Global app state (Zustand).
  - `frontend/src/lib/authStore.ts` – Authentication state.
  - `frontend/src/app/globals.css` & `tailwind.config.ts` – Styling and theming.

This should give you a complete map of the project so you can confidently read, modify, and extend any part of the system.