# Harvester v2 — CLI `harv`

Вторая версия продукта. Задача идёт по восьми стадиям — от первичного
разбора до ревью; каждую стадию исполняет агент в отдельном чате, а CLI
держит состояние, очереди и историю.

**Разделение.** Движок — в этом каталоге. Рантайм каждого проекта — в
`<проект>/.notes/`. Один и тот же движок обслуживает любое число
проектов.

**Зависимостей нет.** Python 3.11+ и только стандартная библиотека:
`argparse`, `json`, `pathlib`, `subprocess`, `unittest`.

---

## Быстрый старт

```bash
make install                               # обёртка dist/harv
ln -sf "$PWD/dist/harv" ~/.local/bin/harv  # чтобы harv был в PATH

harv init /path/to/my/project --personal   # или --work
harv create "Описание задачи"              # создаст HARV-001 в стадии intake
harv status HARV-001
```

Без установки CLI запускается напрямую: `app/src/main --help`.

---

## Модель работы

Восемь стадий, сгруппированных в четыре группы — по группе на чат:

| Группа | Стадии | Роли |
|---|---|---|
| `plan` | `intake` → `analysis` → `architecture` | product-owner, analyst, architect |
| `dev` | `backend`, `frontend`, `integration` | соответствующие разработчики |
| `testing` | `test` | tester |
| `review` | `review` | reviewer |

**Правило одного писателя.** Чат берёт только те задачи, у которых
`current_stage` совпадает с его стадией. Перед записью агент перечитывает
`task.json` и сверяет `runtime.revision`, `current_stage` и `lease`
(TTL 120 минут); после записи увеличивает `revision`, добавляет событие
и переносит `task_id` между `queue.json` стадий. Контракт описан в
`store/examples/notes/tasks/backlog/stages.json`.

Поэтому четыре чата можно держать открытыми одновременно: они физически
не могут взять одну задачу.

### Активация роли

Откройте новый чат (Claude Code или Codex) и напишите ключевое слово,
затем ID задачи:

| Слово | Группа | Стадии |
|---|---|---|
| `harv-planning` | plan | `intake` → `analysis` → `architecture` |
| `harv-dev` | dev | `backend` → `frontend` → `integration` |
| `harv-testing` | testing | `test` |
| `harv-review` | review | `review` |

Ключевое слово перехватывает хук `UserPromptSubmit`
(`ai/adapters/claude-hook`) и подкладывает в контекст инструкции роли.

---

## Команды

Всего 24 команды, у каждой есть флаг `--json` для машиночитаемого вывода
(`{ok, command, data|error}`).

### Проекты

```bash
harv init /path --work | --personal [--force]   # создать .notes/, подключить проект
harv use personal/my-app                        # переключить активный проект
```

`harv init` создаёт `.notes/` из `store/examples/notes/`, кладёт симлинк в
`projects/work/` или `projects/personal/` и делает проект активным. Флаги
`--backend`, `--ui`, `--docs` задают состав стадий.

### Задачи

```bash
harv create "Описание" [--epic my-epic] [--task-id HARV-007]
harv status HARV-001
harv list                     # все задачи
harv queues                   # очереди по стадиям
harv artifacts HARV-001         # артефакты задачи
harv events HARV-001            # журнал событий
```

### Продвижение

```bash
harv take HARV-001 --stage intake --owner planning-terminal
harv move HARV-001 --to analysis --owner planning-terminal
harv advance HARV-001 --to analysis --expect-revision 3
harv release HARV-001
harv add-artifact HARV-001 --type brief --path history/briefs/...
harv retry HARV-001
```

`move` переносит задачу как есть. **`advance`** — валидирующая передача:
проверяет, что переход разрешён картой стадий, и принимает
`--expect-revision` для оптимистичной блокировки — если другой чат успел
изменить задачу, команда откажет вместо того, чтобы перезаписать чужую
работу.

### Параллельная разработка

```bash
harv fanout HARV-001 --branch backend --branch frontend --policy strict
```

**`fanout`** разводит задачу по нескольким стадиям группы `dev`
одновременно и ставит барьер на соединении: следующая стадия начнётся,
когда закончатся все обязательные ветки. `--optional` помечает ветку
необязательной, `--policy best-effort` разрешает продолжить при падении
одной из них.

### Вопросы и инциденты

```bash
harv questions list | add | answer | close
harv incidents list | show | resolve
```

### Целостность

```bash
harv validate      # проверить согласованность .notes/
harv repair        # безопасно починить расхождения очередей и lease
harv sync-index    # пересобрать tasks.json
```

### Групповые сводки

```bash
harv planning | dev | testing | review    # дамп состояния по группе
harv run HARV-001                            # запуск sub-agent через адаптер провайдера
```

---

## Makefile

```bash
make install     # создать обёртку dist/harv
make check       # компиляция Python + smoke-test CLI
make test        # 65 тестов
make projects    # список подключённых проектов
make chat        # интерактивный выбор проекта и группы
```

`make chat` **печатает готовый промпт и команду** для вставки в чат, он
не открывает чат сам. На свежей копии `make projects` и `make chat`
сообщат, что проектов нет, — это ожидаемо, пока не выполнен `harv init`.

---

## Тесты

```bash
make test        # 65 тестов, unittest
```

`PYTHONPATH=app/src` обязателен — пакеты лежат в `app/src`, и без него
падает импорт в `test_cli.py`. Цель `make test` это уже учитывает.

Тесты гоняют настоящий CLI как подпроцесс на копии `store/examples/notes`
во временном каталоге: `test_runtime.py` (28), `test_fanout.py` (8),
`test_handoff.py` (11), `test_incidents.py` (8), `test_runner.py` (7),
`test_cli.py` (3).

---

## Структура

```
backend/
  app/src/
    agentforge_notes/      harv — 24 команды
    agentforge_launcher/   forge — выбор проекта, сборка промпта
    main, forge            запуск без установки пакета
  app/tests/               65 тестов
  ai/
    agents/                роли: business-analyst, разработчики, reviewer, tester
    skills/                business-analysis, notes-runtime
    workflows/             business-analysis, software-delivery
    adapters/
      claude-hook          хук UserPromptSubmit — активация роли по слову
      harv-gate            хук PreToolUse — проверка перед записью
  store/examples/notes/    скелет .notes/ для harv init
  templates/               заготовка под template init / update (пока пусто)
  projects/{work,personal}/  симлинки на проекты, в git не попадают
```

## Структура `.notes/`

```
<project>/.notes/
  tasks/backlog/
    tasks.json              индекс задач
    stages.json             карта стадий, протокол, каталог статусов
    plan/ dev/ testing/ review/
      instructions.md
      stages/<stage>/queue.json
  history/tasks/<TASK_ID>/
    task.json               runtime, revision, события, артефакты
    source.txt              исходное описание
```

---

## Провайдеры LLM

| Провайдер | Переменная окружения |
|---|---|
| Claude | `ANTHROPIC_API_KEY` |
| OpenAI / Codex | `OPENAI_API_KEY` |

Провайдер выбирается при `make chat` или флагом `forge --provider`.
Сам `harv` в сеть не ходит: это машина состояний над файлами, и все 65
тестов проходят без каких-либо ключей.
