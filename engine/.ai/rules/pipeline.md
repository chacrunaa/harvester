# Pipeline Rules

Универсальные правила AI-pipeline. Применяются ко всем агентам и фазам.

---

## 1. Коммуникация через файлы

Агенты общаются **только через файлы**. Прямые вызовы агент → агент запрещены.

- Агент A записывает файл → Harvester обнаруживает → Harvester вызывает агент B
- Порядок: запись файла → обновление pipeline-state.json → следующий агент

## 2. pipeline-state.json — единственный источник состояния

```json
{
  "task_id": "...",
  "phase": "business | systemic | development | testing",
  "agents": {
    "agent-name": "pending | in_progress | done | failed"
  }
}
```

- Агент обновляет свой статус **после** записи всех выходных файлов
- Следующая фаза стартует только когда **все** агенты текущей фазы = "done" (AND-gate)
- Никто кроме самого агента не обновляет его статус

## 3. experience.md — память агента

- Существует с первого прогона, пуст в начале
- Агент читает его **до** начала работы
- Агент обновляет его **после** завершения работы
- Формат свободный, но структурированный по задачам (task-id + дата)

## 4. qna.json — единственный способ задать вопрос пользователю

Агент не додумывает критические данные — он задаёт вопросы через qna.json.

```json
{
  "status": "waiting",
  "questions": [
    {
      "id": "q1",
      "question": "...",
      "options": ["..."] // опционально
    }
  ]
}
```

После ответа пользователя: `"status": "answered"`, появляется поле `"answers"`.

## 5. Clarifications — асинхронный запрос к другому агенту

Если backend/frontend/qa/penetration не понимает spec — они пишут вопросы в:
`clarifications/{recipient}.md`

Analyst читает и отвечает в: `clarifications/{requester}-answers.md`

Clarification не блокирует pipeline. Агент продолжает остальную работу.

## 6. Routing — Harvester копирует файлы по маршрутам

Агент пишет в свою директорию. Harvester копирует в директорию получателя.

Пример:
```
market-analyst пишет: .ai/chats/business/market-analyst/report.md
Harvester копирует: .ai/chats/business/product-manager/reports/market-analyst.md
```

Маршруты описаны в route-map каждого агента. Агент не знает о маршрутах.

## 7. Неизменяемость входных файлов

Агент **никогда не изменяет** входные файлы (cross-brief, spec, briefs от других).
Только свои выходные файлы и experience.md.

## 8. Идемпотентность

При повторном запуске агент перезаписывает выходные файлы (не дописывает).
Exception: experience.md — только дописывать новые записи.

## 9. Статус "failed"

Если агент не смог выполнить задачу (нет критических данных, внутренняя ошибка):
```json
pipeline-state.json → agents["name"] = "failed"
```

office-manager обнаруживает failed и пишет в incidents.md.
Pipeline не продолжается пока failed агент не будет перезапущен.

## 10. Формат имён файлов

- snake_case для имён файлов: `cross-brief.md`, `brief-business.md`
- Директории: строчные, дефис как разделитель: `product-manager/`, `qa-lead/`
- ID задач: верхний регистр + дефис + номер: `TF-001`, `AF-007`
