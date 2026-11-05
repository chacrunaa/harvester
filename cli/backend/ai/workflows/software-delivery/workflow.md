# Workflow: software-delivery

Reusable staged workflow for project implementation tasks.

Project-specific `.notes/tasks/backlog/stages.json` is the local source of
truth. This document defines the reusable default shape.

## Stages

```text
planning -> discovery -> development -> testing -> review -> done
```

## Default Roles

- planning: product-owner
- discovery: analyst, architect
- development: backend-developer, frontend-developer
- testing: tester
- review: reviewer

## Required Shared Behavior

All stage agents use:

```text
ai/skills/notes-runtime/SKILL.md
ai/agents/common/notes-stage-worker.md
```

## Project Responsibility

Each project `.notes` directory defines:

- task id format;
- actual stage ids and directories;
- required inputs and outputs;
- transition rules;
- project-specific stage instructions;
- artifact naming conventions.

Do not hard-code project-specific paths in reusable agents.
