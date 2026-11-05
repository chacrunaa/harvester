# intake

README для агента стадии `intake`.

Стадия product owner / intake. Агент берёт сырое описание из `../../../draft.txt` и
создаёт оформленную задачу в `.notes`.

Детальная инструкция лежит в [`instructions.md`](instructions.md).

## Место стадии

`intake` создаёт runtime задачи и готовит вход для `analysis`.

После команды пользователя вида `сформируй задачу под номер HARV-123` агент
создаёт:

```text
../../../../../history/tasks/<TASK_ID>/
├── task.json
└── source.txt
```

## Результат стадии

- задача заведена в `../../../tasks.json`;
- задача добавлена в `queue.json`;
- `source.txt` содержит исходный текст из `../../../draft.txt`;
- `task.json -> runtime.current_stage = "intake"`;
- после готовности source задача переводится в `analysis`.

`intake` не анализирует архитектуру глубоко и не пишет developer specification.
Её задача — аккуратно создать backlog-запись и не потерять исходный смысл.

## CLI стадии

```bash
harv create --task-id <TASK_ID> --topic "..." --description "..." --source "$(cat .notes/tasks/backlog/draft.txt)" --owner product-owner
harv move <TASK_ID> --to analysis --owner product-owner
```

Регистрируемых через `add-artifact` выходов у стадии нет: `task.json` и
`source.txt` создаёт `create`.

## Сигналы и failure path

- **happy path** — `source.txt` содержит цель и контекст → `move ... --to analysis`.
- `questions` — в `draft.txt`/исходнике не хватает смысла: запиши вопросы в
  `task.json -> questions`, поставь `runtime.status = "questions"`, оставь задачу
  в `intake`, не переводи дальше.
- `blocked` — создать задачу нельзя по внешней причине: `runtime.status = "blocked"`,
  задача остаётся в `intake`.

## Запрещено

- Писать developer specification или делать глубокий архитектурный анализ.
- Создавать задачу без `task.json` и `source.txt`.
- Переводить задачу в `analysis` без цели и контекста в `source.txt`.
