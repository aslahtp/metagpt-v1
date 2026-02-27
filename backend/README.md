# MetaGPT Backend

FastAPI backend for the MetaGPT agentic system.

## Quick Start

```bash
# Create environment and install dependencies
uv sync

# Copy environment file
cp .env.example .env
# Edit .env and add your GOOGLE_API_KEY

# Run the server
uv run serve

# If you renamed the project directory and see "Failed to canonicalize script path",
# recreate the venv: remove the backend/.venv folder, then run `uv sync` again.

# Run tests
uv run pytest
```

## Project Structure

```
app/
├── main.py          # FastAPI application entry point
├── config.py        # Application settings (LLM, projects dir, debug, etc.)
├── db.py            # Database/session setup (if enabled)
├── auth.py          # Authentication helpers and dependencies
├── api/             # FastAPI routing layer
│   ├── router.py    # Top-level API router
│   └── endpoints/   # Versioned endpoint modules (/api/v1/*)
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
│   └── gemini.py    # Google Gemini configuration via LangChain
├── models/          # Persistence/domain models (projects, users)
├── schemas/         # Pydantic models (API + agents)
├── services/        # Business logic (pipeline, chat, sandbox)
├── sop/             # Standard Operating Procedures
├── storage/         # File and project storage helpers
└── rag/             # Retrieval-augmented generation utilities
```

## LLM Configuration

All agents use Google Gemini LangChain:

```python
from app.llm import get_llm, get_llm_with_structured_output

# Get base LLM
llm = get_llm()

# Get LLM with structured output
from app.schemas.agents import ManagerOutput
llm = get_llm_with_structured_output(ManagerOutput)
```

Configuration is in `app/config.py` and can be overridden via environment variables.

## API Documentation

Once running, visit:

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
- Health check: http://localhost:8000/health

## Testing

```bash
# Run all tests
uv run pytest

# Run with coverage
uv run pytest --cov=app

# Run specific test file
uv run pytest tests/test_api.py
```
