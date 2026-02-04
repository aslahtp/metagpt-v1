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
├── agents/          # SOP-driven agent implementations
│   ├── base.py      # Base agent class
│   ├── manager.py   # Manager Agent
│   ├── architect.py # Architect Agent
│   ├── engineer.py  # Engineer Agent
│   └── qa.py        # QA Agent
├── api/             # FastAPI routes
│   └── endpoints/   # API endpoint modules
├── graph/           # LangGraph orchestration
│   ├── state.py     # Pipeline state definition
│   └── orchestrator.py  # Agent pipeline
├── llm/             # LLM configuration
│   └── gemini.py    # Gemini 3 Flash setup
├── schemas/         # Pydantic models
├── services/        # Business logic
├── sop/             # Standard Operating Procedures
├── storage/         # File and project storage
└── main.py          # Application entry point
```

## LLM Configuration

All agents use Google Gemini 3 Flash via LangChain:

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
