# Templates

`templates/` is the source area for Harvester bootstrap templates. These
templates are copied into target projects by future `template init` and
`template update` commands.

## Expected Shape

Each project template should live under its own directory:

```text
templates/<template_id>/.notes/
```

After init, that `.notes` tree is copied to:

```text
<target-project>/.notes/
```

The current MVP template should contain:

- `.notes/manifest.json` with template/runtime metadata;
- `.notes/README.md` explaining the target runtime;
- `.notes/tasks/backlog/**` with stage catalog, protocol, group/stage
  instructions, empty queues and empty experience files;
- `.notes/history/**` with empty archive directories.

Templates must not contain real task runtime artifacts, reports, chats, memory
or demo tasks unless a future command asks for demo data explicitly.

## Template Types

Expected starter templates are roughly:

- `generic-codebase` - default software project template;
- `backend-service` - API/backend-focused project template;
- `frontend-app` - UI/frontend-focused project template;
- `docs-project` - documentation-heavy project template.

The exact catalog is defined by future template tasks, but every template should
use the same `.notes` runtime protocol so stages behave consistently across
projects.

## Update Policy

Template updates may change only template-owned files such as protocol,
runtime schema, stage catalog and stage instructions. Updates must preserve
runtime-owned data:

- `.notes/tasks/backlog/tasks.json`;
- non-empty stage queues;
- `.notes/history/**`;
- task artifacts, role memory, chats, runs and incidents.

See `docs/architecture/notes-template.md`, `docs/specifications/TASK-9.md` and
`docs/flow/structure.md` for the detailed template contract.
