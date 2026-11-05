# Skill Pack: business-analysis

Reusable business-analysis instructions for product and business discovery.

## Contents

- `tasks/` - high-level task pipeline from input review to final analytical conclusion.
- `instructions/main/` - document-level instructions for the main analysis package.
- `instructions/domains/` - domain-specific extensions.
- `expected-outputs/` - reusable contracts for deliverable quality and structure.

## Usage

Use this pack when a project needs structured business analysis from source
materials.

Project data should stay in the target project, for example:

```text
data/input/
data/info/
questions/
data/output/
```

Do not write project outputs into `ai/skills/business-analysis`.

## Expected Flow

1. Check completeness of source materials.
2. Ask clarifying questions when critical context is missing.
3. Build or update `data/output/00-business-context.md`.
4. Produce the main analysis package.
5. Add domain analysis when relevant.
6. Produce a final analytical conclusion.

## Chat Entrypoint

For a standalone business-analysis chat, use:

```text
ai/chats/business-analyst-start.md
```
