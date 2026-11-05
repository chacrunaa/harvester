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
