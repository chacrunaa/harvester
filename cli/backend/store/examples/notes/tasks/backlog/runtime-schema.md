# Runtime JSON Schema Notes

Это человекочитаемое описание схемы. Формальный JSON Schema можно добавить позже, когда протокол стабилизируется.

## `tasks.json`

Лёгкий индекс задач и краткое отображение текущего runtime status/stage.
Статичная карта стадий вынесена в `stages.json`, полное runtime-состояние задач
хранится в `history/tasks/<TASK_ID>/task.json`.

Ключевые поля:

- `schema_version` — версия файлового протокола.
- `stages_link` — ссылка на `stages.json`.
- `epics` — группировка задач.
- `tasks` — словарь задач по `task_id` с кратким runtime-отображением.
- `tasks.<TASK_ID>.current_stage`, `status`, `revision`, `runtime_updated_at` —
  лёгкое отображение текущего runtime-состояния для backlog-обзора. Полная
  версия состояния всё равно хранится в `history/tasks/<TASK_ID>/task.json`.
  Это денормализованный snapshot: источник истины — `task.json`, а `harv validate`
  следит, чтобы snapshot не расходился с ним.

## `stages.json`

Файл описывает pipeline, роли, допустимые статусы, обязательные входы/выходы и переходы.

Ключевые поля:

- `protocol` — общие правила работы.
- `status_catalog` — допустимые статусы.
- `stages` — разрешённые стадии и переходы.

Stage:

```json
{
  "id": "intake",
  "group": "plan",
  "role": "product-owner",
  "directory": "plan/stages/intake",
  "instructions": "plan/stages/intake/instructions.md",
  "required_inputs": [],
  "required_outputs_on_success": [],
  "transitions": {
    "success": {
      "next_stage": "analysis",
      "next_status": "ready_for_next_stage"
    }
  }
}
```

Index entry:

```json
{
  "task_id": "HARV-123",
  "topic": "Название",
  "description": "Краткое описание",
  "history_dir": "../../history/tasks/HARV-123",
  "task_link": "../../history/tasks/HARV-123/task.json",
  "current_stage": "analysis",
  "status": "ready_for_next_stage",
  "revision": 2,
  "runtime_updated_at": "2026-06-04T19:30:00+03:00"
}
```

## `history/tasks/<TASK_ID>/task.json`

Единый небольшой JSON задачи: metadata, runtime, artifacts index, questions и events.

```json
{
  "task_id": "HARV-123",
  "runtime": {
    "current_stage": "analysis",
    "status": "new",
    "revision": 1,
    "lease": null
  },
  "artifacts": {
    "briefs": [],
    "specifications": [],
    "reports": [],
    "memory": [],
    "chats": [],
    "questions": []
  },
  "questions": [],
  "events": []
}
```

## Stage Index JSON

Все stage queue JSON имеют общий верхний формат:

```json
{
  "schema_version": 1,
  "stage": "analysis",
  "role": "analyst",
  "items": [
    {
      "task_id": "HARV-123",
      "task_link": "../../../../../history/tasks/HARV-123/task.json",
      "priority": 100
    }
  ]
}
```

## Questions

Вопросы живут в `history/tasks/<TASK_ID>/task.json -> questions` как плоский
список. Управляются командами `harv questions add/answer/close/list`.

```json
{
  "id": "Q-HARV-123-001",
  "status": "open",
  "created_at": "2026-06-03T19:30:00+03:00",
  "answered_at": null,
  "question": "...",
  "answer": null,
  "actor": "analyst"
}
```

`status`: `open` → `answered` (после `answer`) → `closed` (после `close`).
