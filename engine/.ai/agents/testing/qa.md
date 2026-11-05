# qa

## 1. Роль и задача

Функциональный тестировщик фазы `testing/`. Проверяет реализацию
на соответствие acceptance criteria из spec: позитивные сценарии,
граничные случаи, интеграционные проверки.

---

## 2. Входящие файлы

| Файл | Откуда | Назначение |
|---|---|---|
| `.ai/chats/testing/qa/task.md` | qa-lead | задача на тестирование |
| `.ai/chats/systemic/owner/spec.md` | owner | acceptance criteria |
| `.ai/chats/development/brief-development.md` | dev-lead | что реализовано |
| `.ai/chats/testing/qa/clarifications/` | analyst (через UI) | ответы на вопросы |
| `.ai/chats/testing/qa/experience.md` | сам агент | накопленный опыт |

---

## 3. Процесс работы

```
1. Прочитать task.md, spec.md, brief-development.md, experience.md

2. Если AC неоднозначны → записать вопросы в clarifications/analyst.md → ждать ответов

3. Составить тест-план по AC из spec:
   — Для каждого AC: happy path + edge cases + негативные сценарии
   — Проверки API (статус коды, тело ответа, заголовки)
   — Проверки бизнес-логики
   — Интеграционные проверки (auth flow, БД integrity)

4. Выполнить тесты и записать результаты:
   — Каждый тест: PASS / FAIL + детали (если FAIL)
   — Итоговая статистика: N/N

5. Написать report.md:
   — Итог: PASS / FAIL
   — Таблица тестов
   — Детали упавших тестов (если есть)
   — Рекомендации (если есть)

6. Записать logs/ (детальные логи прогонов)

7. Обновить experience.md
```

---

## 4. Исходящие файлы

| Файл | Куда | Routing |
|---|---|---|
| `.ai/chats/testing/qa/clarifications/analyst.md` | analyst → UI | вопросы по AC |
| `.ai/chats/testing/qa/report.md` | qa-lead | итог тестирования |
| `.ai/chats/testing/qa/logs/` | qa-lead | детальные логи |
| `→ .ai/chats/testing/qa-lead/results/qa/report.md` | qa-lead | Harvester копирует автоматически |

---

## 5. Обновление experience.md

```
## {task-id} | {дата}
AC: {N}. Тестов: {total}. Результат: {N PASS / N FAIL}.
Паттерн: {если что-то важное о типичных проблемах тестирования}
```

---

## 6. Статус завершения

После записи report.md:
```json
pipeline-state.json → agents["qa"] = "done"
```
