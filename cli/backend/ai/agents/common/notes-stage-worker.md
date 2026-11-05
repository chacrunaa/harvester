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
