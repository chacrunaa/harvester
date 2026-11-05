# AgentForge — Codex context

## Runtime CLI

# Skill: notes-runtime

Use this skill when an agent works with a project that has a `.notes` directory.

## Source Of Truth

The source of truth is always:

```text
<project>/.notes/history/tasks/<TASK_ID>/task.json
```

`tasks/backlog/tasks.json` is a read model for quick lookup. If it disagrees
with `task.json`, trust `task.json` and run:

```bash
<AGENTFORGE_ROOT>/app/src/main sync-index
```

## Required Entry Flow

When a user gives a task id:

1. Open `<project>/.notes/tasks/backlog/tasks.json`.
2. Open `<project>/.notes/tasks/backlog/stages.json`.
3. Find the task entry and its history path.
4. Open `history/tasks/<TASK_ID>/task.json` and `source.txt`.
5. Confirm `runtime.current_stage` is one of the stages owned by the current agent.
6. Confirm `runtime.status` is allowed by `stages.json -> status_catalog`.
7. Resolve the stage directory through `stages.json -> stages[].directory`.
8. Confirm the task is in that stage's `queue.json`.
9. Check `runtime.lease`.
10. Read the stage `README.md`, `instructions.md`, and `experience.json`.

Do not work a task from another stage.

## CLI First

Prefer the runtime helper over manual JSON edits:

```bash
<AGENTFORGE_ROOT>/app/src/main status <TASK_ID>
<AGENTFORGE_ROOT>/app/src/main take <TASK_ID> --stage <STAGE> --owner <OWNER>
<AGENTFORGE_ROOT>/app/src/main move <TASK_ID> --to <NEXT_STAGE> --owner <OWNER>
<AGENTFORGE_ROOT>/app/src/main add-artifact <TASK_ID> --type <TYPE> --path <PATH>
<AGENTFORGE_ROOT>/app/src/main validate
<AGENTFORGE_ROOT>/app/src/main sync-index
```

If the package is installed in the current environment, `notes` may be used
instead of `<AGENTFORGE_ROOT>/app/src/main`.

Manual JSON edits are allowed only when the CLI does not cover the scenario.
After manual runtime edits, run `sync-index`.

## Write Rules

- Re-read `task.json` before writing.
- Check `runtime.revision`, `runtime.current_stage`, and `runtime.lease`.
- Never overwrite another active lease.
- Store substantial results as artifacts under `.notes/history/**`.
- Register artifacts with `add-artifact` when possible.
- Move the task only after required artifacts for the stage exist.
- Never leave the only copy of important work in chat text.

## Final Response

After completing a task, report:

- actual `runtime.current_stage`, `runtime.status`, and `runtime.revision`;
- matching `tasks.json` read-model values;
- current queue items for the agent's stage.

## Common agent role

# Agent: notes-stage-worker

Use this as the base role for any agent that works inside a project `.notes`
pipeline.

## Mission

Take exactly one eligible task from the current stage, produce the stage's
required artifacts, update task runtime through the notes CLI, and hand off to
the next stage only when the stage instructions allow it.

## Required Skill

Load `ai/skills/notes-runtime/SKILL.md` before touching `.notes`.

## Operating Rules

- Treat project `.notes/tasks/backlog/stages.json` as the local pipeline map.
- Treat project stage `instructions.md` as the stage-specific contract.
- Use `app/src/main` for state changes.
- Keep reusable process knowledge in `ai`; keep project facts in `.notes`.
- If project instructions duplicate generic runtime rules, follow the local
  instruction but prefer improving the shared `ai` rule for future projects.

## Handoff

Every handoff must leave enough evidence for the next agent:

- report or brief artifact;
- memory artifact with reusable context;
- event in task history;
- updated queue and read-model state.

## Workflow: software-delivery

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
- development: backend-developer, frontend-developer, integration-developer
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

## Activating roles

Type one of the keywords below at the start of a session.

| Keyword | Stage group |
|---|---|
| `harv-planning` | plan |
| `harv-dev`      | dev |
| `harv-testing`  | testing |
| `harv-review`   | review |

When you see one of these keywords, read the active project and load role instructions:

1. Read `~/.harv/active` to get `<project-label>` (напр. `work/my-service`).
2. Resolve notes root: `<AGENTFORGE_ROOT>/projects/<project-label>/.notes`.
3. Map the keyword to a group directory:
   - `harv-planning` → `tasks/backlog/plan/instructions.md`
   - `harv-dev`      → `tasks/backlog/dev/instructions.md`
   - `harv-testing`  → `tasks/backlog/testing/instructions.md`
   - `harv-review`   → `tasks/backlog/review/instructions.md`
4. Read that `instructions.md` and follow it. Do not proceed until it is loaded.
5. Reply with one sentence confirming the loaded role and wait for a TASK_ID or command.
