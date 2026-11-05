# AI Workspace

This directory stores reusable AI assets for AgentForge-managed projects.

Runtime/application code lives in `app/src`. Do not put executable project
runtime code here.

## Layout

- `agents/` - reusable agent role definitions.
- `skills/` - reusable operating instructions for specific work types.
- `workflows/` - reusable pipeline descriptions that project `.notes` folders can reference.
- `templates/` - starter documents for new agents, skills, reports, and memories.

Project-specific state, queues, task history, and stage configuration stay in
each project's `.notes` directory.

## Boundary

Use `ai` for shared AI behavior:

- how an agent enters a `.notes` task;
- how leases, revisions, artifacts, and transitions work;
- how business-analysis, development, testing, review, and documentation agents operate;
- reusable prompts, checklists, and report templates.

Use project `.notes` for local facts:

- task IDs and queues;
- `stages.json`;
- project-specific stage instructions;
- task history and artifacts;
- project-specific experience and memory.
