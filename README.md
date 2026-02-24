# MetaGPT

A production-ready agentic code generation system. This system uses SOP-driven autonomous agents to transform natural language prompts into fully functional codebases.

## Architecture

```
User Prompt → Manager → Architect → Engineer → QA → Generated Project
```

### Agent Pipeline

1. **Manager Agent**: Converts natural language prompts into structured requirements
2. **Architect Agent**: Designs system architecture and file structure
3. **Engineer Agent**: Generates production-ready code files
4. **QA Agent**: Creates test cases and validates code quality

### LLM

All agents use **Google Gemini 3 Flash** via LangChain. No OpenAI, no Anthropic, no fallback models.

## Tech Stack

### Backend

- **Python 3.11+**
- **FastAPI** - High-performance async API
- **LangChain** - LLM orchestration
- **LangGraph** - Agent workflow graphs
- **uv** - Fast Python package manager

### Frontend

- **Next.js 14** - React framework with App Router
- **TypeScript** - Type safety
- **Tailwind CSS** - Utility-first styling
- **Dark theme** by default

## Project Structure

```
metagpt-v1/
├── backend/
│   ├── app/
│   │   ├── main.py        # FastAPI app entry point
│   │   ├── config.py      # Application settings (LLM, projects dir, debug, etc.)
│   │   ├── db.py          # Database/session setup (if enabled)
│   │   ├── auth.py        # Authentication helpers and dependencies
│   │   ├── api/           # FastAPI routing layer
│   │   │   ├── router.py  # Top-level API router
│   │   │   └── endpoints/ # /api/v1/* endpoint modules
│   │   ├── agents/        # SOP-driven agents (Manager, Architect, Engineer, QA)
│   │   ├── graph/         # LangGraph pipeline state and orchestrator
│   │   ├── llm/           # Central Gemini configuration
│   │   ├── models/        # Persistence/domain models (projects, users)
│   │   ├── schemas/       # Pydantic schemas (API + agents)
│   │   ├── services/      # Business logic (pipeline, chat, sandbox)
│   │   ├── sop/           # Agent SOP definitions
│   │   ├── storage/       # File & project storage helpers
│   │   └── rag/           # Retrieval-augmented generation utilities
│   ├── tests/
│   └── pyproject.toml
├── frontend/
│   ├── src/
│   │   ├── app/           # Next.js routes and layouts
│   │   ├── components/    # React components
│   │   └── lib/           # API client, state, utilities
│   ├── package.json
│   └── tailwind.config.ts
└── docs/                  # Architecture & technical documentation
```

## Quick Start

### Prerequisites

- Python 3.11+
- Node.js 18+
- [uv](https://github.com/astral-sh/uv) (recommended) or pip
- Google API Key for Gemini

### Backend Setup

```bash
cd backend

# Create .env file
cp .env.example .env
# Edit .env and add your GOOGLE_API_KEY

# Install dependencies with uv
uv sync

# Or with pip
pip install -e .

# Run the server
uv run uvicorn app.main:app --reload
# Or: python -m uvicorn app.main:app --reload

# Server runs at http://localhost:8000
# API docs at http://localhost:8000/docs
```

### Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Run development server
npm run dev

# Frontend runs at http://localhost:3000
```

## API Endpoints

### Projects

- `POST /api/v1/projects` - Create a new project
- `GET /api/v1/projects` - List all projects
- `GET /api/v1/projects/{id}` - Get project details
- `GET /api/v1/projects/{id}/reasoning` - Get agent reasoning

### Pipeline

- `POST /api/v1/pipeline/run` - Create project and run pipeline
- `POST /api/v1/pipeline/stream` - Stream pipeline execution (SSE)
- `GET /api/v1/pipeline/{id}/status` - Get pipeline status
- `GET /api/v1/pipeline/{id}/artifacts` - Get all agent outputs

### Files

- `GET /api/v1/files/{id}/tree` - Get file tree
- `GET /api/v1/files/{id}/content/{path}` - Get file content
- `PUT /api/v1/files/{id}/content/{path}` - Update file content

### Chat

- `POST /api/v1/chat/{id}` - Send chat message for iteration
- `GET /api/v1/chat/{id}/history` - Get chat history

## Example Usage

### Create a Project via API

```bash
curl -X POST http://localhost:8000/api/v1/pipeline/run \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Build a todo app with React and a REST API backend"}'
```

### Stream Pipeline Execution

```bash
curl -N http://localhost:8000/api/v1/pipeline/stream \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Build a blog platform with Next.js"}'
```

## Agent SOPs

Each agent follows a Standard Operating Procedure (SOP) that defines:

- **Role**: Agent identity and responsibility
- **Objective**: What the agent must accomplish
- **Inputs**: Expected input data
- **Outputs**: Required output structure
- **Constraints**: Rules and limitations
- **Quality Checklist**: Validation criteria

SOPs are defined in `backend/app/sop/definitions.py`.

## Configuration

### Environment Variables

```bash
# Required
GOOGLE_API_KEY=your-api-key

# Optional
LLM_MODEL=gemini-2.0-flash
LLM_TEMPERATURE=0.7
LLM_MAX_TOKENS=8192
PROJECTS_DIR=./projects
DEBUG=false
```

### LLM Configuration

The LLM is centrally configured in `backend/app/llm/gemini.py`. All agents use this single configuration:

```python
from app.llm import get_llm

llm = get_llm()  # Returns configured Gemini 3 Flash instance
```

## Development

### Running Tests

```bash
cd backend
uv run pytest
```

### Type Checking

```bash
# Backend
cd backend
uv run mypy app

# Frontend
cd frontend
npm run type-check
```

### Linting

```bash
# Backend
cd backend
uv run ruff check app

# Frontend
cd frontend
npm run lint
```

## Features

### Implemented

- [x] SOP-driven agents (Manager, Architect, Engineer, QA)
- [x] LangGraph orchestration
- [x] Gemini 3 Flash integration
- [x] File generation and storage
- [x] Streaming pipeline execution
- [x] Chat-based iterations
- [x] React/Next.js project detection
- [x] Dark theme UI
- [x] File explorer and code viewer
- [x] Execution timeline
- [x] Agent output visualization

### Roadmap

- [ ] Live preview for React projects
- [ ] Git integration
- [ ] Deployment support
- [ ] Multiple project templates
- [ ] Collaborative editing
- [ ] Version history

## License

MIT
