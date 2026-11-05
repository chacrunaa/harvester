# Claude Runtime Bridge

`.claude/**` — тонкий runtime-слой, он ничего не хранит сам:

- `settings.json` — подключение хуков:
  - `UserPromptSubmit` → `ai/adapters/claude-hook` — активация роли по
    ключевому слову (`harv-planning`, `harv-dev`, `harv-testing`, `harv-review`)
  - `PreToolUse` → `ai/adapters/harv-gate` — проверка перед записью

Канонические источники:

- `ai/` — роли агентов, навыки, воркфлоу, адаптеры
- `<проект>/.notes/` — состояние задач целевого проекта

Принцип: `.claude/**` ссылается на `ai/**`, и любой провайдер (claude,
codex и другие) подключается к тому же `ai/`.
