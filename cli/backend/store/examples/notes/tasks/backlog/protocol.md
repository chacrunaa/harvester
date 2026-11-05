# Agent Chat Runtime Protocol

## Модель

Каждая консоль — group-holder агент, который маршрутизирует во внутреннюю стадию:

- консоль `harv-planning`: `plan` → `intake`, `analysis`, `architecture`;
- консоль `harv-dev`: `dev` → `backend`, `frontend`, `integration`;
- консоль `harv-testing`: `testing` → `testing`;
- консоль `harv-review`: `review` → `review`.

Лёгкий индекс задач хранится в `tasks.json`.
Карта стадий, статусы, обязательные входы/выходы и переходы хранятся в `stages.json`.
Очередь каждой внутренней стадии хранится в `<group>/stages/<stage>/queue.json`.
Полное runtime-состояние и история конкретной задачи хранятся в `history/tasks/<TASK_ID>/`.

## CLI-first

Если нужно изменить состояние задачи, агент должен предпочитать CLI ручной правке JSON:

```bash
harv status HARV-123
harv take HARV-123 --stage analysis --owner analysis-console
harv move HARV-123 --to architecture --owner analysis-console
harv add-artifact HARV-123 --type brief --path history/briefs/analyst/HARV-123.analysis-brief.md
```

Ручная правка JSON допустима только если CLI не покрывает нужный сценарий.

## Правило входа в задачу

Когда пользователь пишет `HARV-123`, агент обязан:

Это считается призывом к действию: задача у агента есть, её нужно взять в
работу в текущей консоли, если она действительно находится на стадии этой
консоли.

1. Прочитать `tasks.json`.
2. Прочитать `stages.json`.
3. Найти `tasks.HARV-123` и `history_dir`.
4. Прочитать `history/tasks/HARV-123/task.json`.
5. Проверить, что `current_stage` совпадает со стадией текущего чата.
6. Проверить, что `status` входит в `stages.json -> status_catalog` и не равен `done`.
7. Проверить, что `HARV-123` есть в `<current_stage>/queue.json`.
8. Проверить `lease`:
   - если `lease = null`, задачу можно взять;
   - если lease принадлежит этому же чату, можно продолжать;
   - если lease принадлежит другому чату и не истёк, задачу брать нельзя.
9. Перечитать `history/tasks/HARV-123/task.json` и `source.txt`.
10. Прочитать `README.md` своей group-holder директории.
11. Работать строго по `instructions.md` своей стадии.

## Lease

Lease нужен, чтобы две консоли не писали одну задачу одновременно.

Пример:

```json
{
  "owner": "analysis-console-1",
  "agent": "analyst",
  "acquired_at": "2026-06-03T19:30:00+03:00",
  "expires_at": "2026-06-03T21:30:00+03:00"
}
```

## Revision

`revision` — простой optimistic lock.

Перед записью агент запоминает текущий `runtime.revision` из `history/tasks/<TASK_ID>/task.json`. Перед финальным обновлением перечитывает `task.json`. Если revision изменился, агент останавливается и не пишет поверх чужой работы.

## Артефакты

Артефакты пишутся в `history/**` по роли и типу артефакта, а
`history/tasks/<TASK_ID>/task.json -> artifacts` хранит только индекс.

Пример:

- brief: `history/briefs/analyst/HARV-123.analysis-brief.md`;
- architect adjustment brief: `history/briefs/architect/HARV-123.analysis-adjustment-brief.md`;
- specification: `history/specifications/HARV-123.developer-spec.md`;
- architecture report: `history/reports/architect/HARV-123.architecture-report.md`;
- backend report: `history/reports/developer/backend/HARV-123.backend-report.md`;
- frontend report: `history/reports/developer/frontend/HARV-123.frontend-report.md`;
- integration report: `history/reports/developer/integration/HARV-123.integration-report.md`;
- developer report: `history/reports/developer/HARV-123.developer-report.md`;
- memory: `history/memory/analyst/HARV-123.md`;
- architect memory: `history/memory/architect/HARV-123.md`;
- backend memory: `history/memory/developer/backend/HARV-123.md`;
- frontend memory: `history/memory/developer/frontend/HARV-123.md`;
- integration memory: `history/memory/developer/integration/HARV-123.md`;
- chat: `history/chats/analyst/HARV-123.jsonl`;
- architect chat: `history/chats/architect/HARV-123.jsonl`;
- backend chat: `history/chats/developer/backend/HARV-123.jsonl`;
- frontend chat: `history/chats/developer/frontend/HARV-123.jsonl`;
- integration chat: `history/chats/developer/integration/HARV-123.jsonl`;
- report: `history/reports/tester/HARV-123.test-report.md`.

## Переходы

Переход разрешён только после создания обязательных артефактов стадии:

| From | To | Условие |
|---|---|---|
| `intake` | `analysis` | Есть `history/tasks/<TASK_ID>/task.json` и `source.txt`. |
| `analysis` | `architecture` | Есть analyst brief и developer specification. |
| `architecture` | `backend` | Есть architecture report; developer specification проверена и при необходимости дополнена. |
| `architecture` | `analysis` | Есть architecture report и architect adjustment brief со статусом `needs_adjustment`. |
| `backend` | `frontend` | Есть backend report и backend memory. |
| `frontend` | `integration` | Есть frontend report и frontend memory. |
| `integration` | `testing` | Есть integration report и общий developer report. |
| `testing` | `review` | Есть test report. |
| `testing` | `backend` | Есть test report и failure brief с результатом `failed`; developer chain запускается заново. |
| `review` | `done` | Есть review report со статусом `accepted`. |
| `review` | `analysis` | Есть review report и analysis adjustment brief со статусом `needs_adjustment`. |
| `review` | `architecture` | Есть review report и architecture adjustment brief со статусом `needs_adjustment`. |
| `review` | `backend` | Есть review report и code adjustment brief со статусом `needs_adjustment`; developer chain запускается заново. |

При переходе агент обновляет:

1. `history/tasks/<TASK_ID>/task.json -> runtime`;
2. `history/tasks/<TASK_ID>/task.json -> events`;
3. `tasks/backlog/tasks.json -> tasks.<TASK_ID>`: `current_stage`, `status`,
   `revision`, `runtime_updated_at`;
4. queue-файл исходной стадии;
5. queue-файл целевой стадии.

Предпочтительный способ:

```bash
harv move HARV-123 --to architecture --owner analysis-console
```

CLI синхронизирует `tasks.json` автоматически. При ручной правке JSON агент
обязан обновить и `history/tasks/<TASK_ID>/task.json`, и лёгкое отображение
статуса в `tasks/backlog/tasks.json`.

## Вопросы

Если агенту не хватает данных, он:

1. Добавляет вопросы в `history/tasks/<TASK_ID>/task.json -> questions`.
2. Добавляет ссылку на вопросы в `history/tasks/<TASK_ID>/task.json -> artifacts.questions`.
3. Ставит `runtime.status = "questions"` в `history/tasks/<TASK_ID>/task.json`.
4. Не переводит задачу дальше, пока ответы не заполнены.

## Запреты

- Нельзя брать задачу из чужой стадии.
- Нельзя менять `current_stage` без обязательных артефактов.
- Нельзя удалять старые артефакты задачи.
- Нельзя перезаписывать историю чата; новый проход добавляется новой записью.
- Нельзя держать результат только в тексте ответа пользователю: всё существенное фиксируется в `.notes`.
