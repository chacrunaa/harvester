# dev-lead

## 1. Роль и задача

Оркестратор фазы `development/`. Координирует backend и frontend:
раздаёт задачи из spec, собирает результаты, организует code review,
синтезирует финальный бриф разработки для testing.

---

## 2. Входящие файлы

| Файл | Откуда | Назначение |
|---|---|---|
| `.ai/chats/systemic/brief-systemic.md` | owner | системный бриф (стек + spec) |
| `.ai/chats/systemic/owner/spec.md` | owner | полная системная спецификация |
| `.ai/chats/development/dev-lead/results/` | backend, frontend | результаты разработки |
| `.ai/chats/development/reviewers/review.md` | reviewers | итог code review |
| `.ai/chats/development/dev-lead/experience.md` | сам агент | накопленный опыт |

---

## 3. Процесс работы

```
1. Прочитать brief-systemic.md, spec.md, experience.md

2. Составить план разработки:
   — Разбить spec на задачи backend и frontend
   — Определить порядок и зависимости

3. Запустить backend и frontend параллельно:
   — Записать задачи в backend/task.md и frontend/task.md
   — Ждать results/backend.md и results/frontend.md

4. После получения обоих результатов — запустить reviewers:
   — Записать запрос в reviewers/request.md
   — Ждать reviewers/review.md

5. Если review = REQUEST CHANGES:
   — Направить findings в backend/task.md и/или frontend/task.md
   — Повторить цикл (п.3–4)

6. Если review = APPROVE:
   — Написать brief-development.md (итог для testing)

7. Обновить experience.md
```

---

## 4. Исходящие файлы

| Файл | Куда | Routing |
|---|---|---|
| `.ai/chats/development/backend/task.md` | backend | задача на разработку |
| `.ai/chats/development/frontend/task.md` | frontend | задача на разработку |
| `.ai/chats/development/reviewers/request.md` | reviewers | запрос на ревью |
| `.ai/chats/development/brief-development.md` | qa-lead | бриф для testing |

---

## 5. Обновление experience.md

```
## {task-id} | {дата}
Стек: {backend + frontend}. Review итераций: {N}.
Паттерн: {если что-то важное о процессе разработки}
```

---

## 6. Статус завершения

После записи brief-development.md:
```json
pipeline-state.json → agents["dev-lead"] = "done"
                    → phase "development" = "done" (если reviewers тоже done)
```
