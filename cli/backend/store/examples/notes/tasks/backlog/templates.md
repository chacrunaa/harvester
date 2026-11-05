# Artifact Templates

Шаблоны не являются обязательным форматом навсегда. Это стартовая договорённость,
чтобы стадии писали совместимые артефакты.

Полный контракт по всем артефактам (назначение, автор, читатель, путь,
`add-artifact` type, критерии достаточности) — в
`<AGENTFORGE_ROOT>/docs/flow/artifact-templates.md`. Ниже — операционные скелеты
самых частых артефактов. Скелеты остальных (architect report, backend/frontend/
integration reports, tester instruction, terminal log, question, failure/adjustment
brief) описаны в том же справочнике.

## Analyst Brief

Путь:

```text
history/briefs/analyst/<TASK_ID>.analysis-brief.md
```

Структура:

```markdown
# <TASK_ID> Analysis Brief

## Цель

## Контекст

## Scope

## Out Of Scope

## Затронутые зоны

## Риски

## Вопросы и ответы

## Acceptance Criteria

## Решение аналитика
Готово к разработке: yes/no.
```

## Developer Specification

Путь:

```text
history/specifications/<TASK_ID>.developer-spec.md
```

Структура:

```markdown
# <TASK_ID> Developer Specification

## Контекст

## Цель

## Обязательный объём работ

## Затронутые слои

## Ограничения

## Acceptance Criteria

## Проверки
```

## Developer Report

Путь:

```text
history/reports/developer/<TASK_ID>.developer-report.md
```

Структура:

```markdown
# <TASK_ID> Developer Report

## Что сделано

## Изменённые файлы

## Проверки

## Ограничения и риски

## Handoff для тестировщика
```

## Test Report

Путь:

```text
history/reports/tester/<TASK_ID>.test-report.md
```

Структура:

```markdown
# <TASK_ID> Test Report

## Проверенный scope

## Команды и результаты

## Evidence

## Непроверенные области

## Итог
passed / failed / blocked
```

## Review Report

Путь:

```text
history/reports/reviewer/<TASK_ID>.review-report.md
```

Структура:

```markdown
# <TASK_ID> Review Report

## Итог
accepted / needs_adjustment

## Проверенные артефакты

## Проверка требований

## Замечания

## Финальное действие
```

## Memory

Путь:

```text
history/memory/<role>/<TASK_ID>.md
```

Структура:

```markdown
# <TASK_ID> <Role> Memory

## Что было важно

## Что повторить в похожих задачах

## Чего избегать
```
