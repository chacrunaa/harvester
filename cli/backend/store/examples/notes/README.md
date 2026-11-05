# Harvester Notes Runtime Prototype

Эта директория содержит файловый runtime для работы нескольких AI-агентов над задачами Harvester.

Ключевые точки входа:

- `tasks/backlog/tasks.json` - индекс задач.
- `tasks/backlog/stages.json` - карта стадий и переходов.
- `tasks/backlog/protocol.md` - общий протокол работы агентов.
- `history/tasks/<TASK_ID>/task.json` - runtime-состояние конкретной задачи.

Документация по текущей концепции лежит в `docs/flow` проекта.
