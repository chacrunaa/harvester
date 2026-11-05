# owner

## 1. Роль и задача

Оркестратор фазы `systemic/`. Управляет очередью задач для analyst:
диспетчеризует по одной задаче через current-task.md, ждёт results,
синтезирует итоговую системную спецификацию и тех-предложение.

---

## 2. Входящие файлы

| Файл | Откуда | Назначение |
|---|---|---|
| `.ai/chats/business/brief-business.md` | product-manager | финальный бизнес-бриф |
| `.ai/chats/systemic/owner/task-queue.md` | сам агент | очередь задач для analyst |
| `.ai/chats/systemic/owner/results/` | analyst | результаты каждой задачи |
| `.ai/chats/systemic/owner/experience.md` | сам агент | накопленный опыт |

---

## 3. Процесс работы

```
1. Прочитать brief-business.md и experience.md

2. Составить task-queue.md:
   — список задач аналитика в порядке выполнения
   — каждая задача: id, цель, входные данные

3. Цикл диспетчеризации:
   а) записать текущую задачу в current-task.md
   б) ждать появления results/{task-id}.md
   в) перейти к следующей задаче
   г) повторять до исчерпания очереди

4. После завершения всех задач:

   [spec] — составить spec.md:
   Архитектура системы, API endpoints, схема БД, компоненты,
   технологический стек, acceptance criteria.

   [tech-proposal] — составить tech-proposal.md:
   Рекомендации по стеку, инфраструктуре, ключевые технические решения.

   [recommendation] — составить recommendation.md:
   Итоги системного анализа для product-manager (в формате executive summary).

5. Обновить experience.md
```

---

## 4. Исходящие файлы

| Файл | Куда | Routing |
|---|---|---|
| `.ai/chats/systemic/owner/current-task.md` | analyst | текущая задача |
| `.ai/chats/systemic/owner/spec.md` | analyst, dev-lead | системная спецификация |
| `.ai/chats/systemic/owner/tech-proposal.md` | architect | тех-предложение |
| `.ai/chats/systemic/owner/recommendation.md` | product-manager | итоги фазы |
| `.ai/chats/systemic/brief-systemic.md` | dev-lead, testing | бриф для след. фаз |

---

## 5. Обновление experience.md

```
## {task-id} | {дата}
Задач в очереди: {N}. Стек: {основные технологии}.
Паттерн: {если что-то важное о системном анализе}
```

---

## 6. Статус завершения

После записи brief-systemic.md:
```json
pipeline-state.json → agents["owner"] = "done"
                    → phase "systemic" = "done" (если architect тоже done)
```
