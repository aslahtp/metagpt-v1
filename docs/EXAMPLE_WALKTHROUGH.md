# Example Walkthrough: Building a Todo App

This document walks through an example of using MetaGPT-Lovable to generate a complete todo application.

## Step 1: Submit the Prompt

Navigate to http://localhost:3000 and enter the following prompt:

```
Build a modern todo app with React for the frontend and a FastAPI backend.
Features:
- Add, edit, and delete todos
- Mark todos as complete
- Filter by status (all, active, completed)
- Persist data to a JSON file
- Clean, minimal UI with dark theme
```

Click "Generate" to start the pipeline.

## Step 2: Watch the Pipeline Execute

You'll see each agent execute in sequence:

1. **Manager Agent** (25%) - Analyzing requirements
2. **Architect Agent** (50%) - Designing architecture
3. **Engineer Agent** (75%) - Generating code
4. **QA Agent** (100%) - Validating quality

Each agent's progress is shown in the timeline on the right panel.

## Step 3: Explore Generated Files

After completion, the file explorer shows all generated files:

```
todo-app/
├── backend/
│   ├── main.py
│   ├── models.py
│   ├── storage.py
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── App.tsx
│   │   ├── components/
│   │   │   ├── TodoList.tsx
│   │   │   ├── TodoItem.tsx
│   │   │   ├── AddTodo.tsx
│   │   │   └── FilterBar.tsx
│   │   ├── api.ts
│   │   └── types.ts
│   ├── package.json
│   └── tailwind.config.js
└── README.md
```

Click any file to view its contents with syntax highlighting.

## Step 4: Review Agent Outputs

Switch to the "Outputs" tab to see detailed agent outputs:

- **Manager**: Requirements, tech stack, constraints
- **Architect**: Components, file structure, API design
- **Engineer**: Generated files, dependencies, setup instructions
- **QA**: Test cases, validation notes, quality score

## Step 5: Iterate with Chat

Expand the chat panel at the bottom and request changes:

```
User: Add a due date field to todos
```

The system will:

1. Classify your intent (which agents need to run)
2. Execute the necessary agents (likely just Engineer for this change)
3. Update only the affected files
4. Show you what changed

## Step 6: Run the Generated Project

To run the generated project locally:

```bash
# Navigate to project files
cd projects/{project-id}/files

# Backend
cd backend
pip install -r requirements.txt
uvicorn main:app --reload

# Frontend (in another terminal)
cd frontend
npm install
npm run dev
```

## Tips

- **Be specific** in your prompts for better results
- **Use the chat** for incremental changes rather than regenerating
- **Check QA output** for potential issues before running
- **View reasoning** to understand agent decisions

## Common Chat Commands

- "Add a new feature..." - Triggers Manager -> Architect -> Engineer
- "Fix the bug in..." - Triggers Engineer only
- "Add tests for..." - Triggers QA only
- "Change the styling..." - Triggers Engineer only
- "Refactor the..." - Triggers Architect -> Engineer
