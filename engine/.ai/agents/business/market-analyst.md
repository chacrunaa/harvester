# market-analyst

## 1. Роль и задача

Аналитик фазы `business/`. Исследует рыночный контекст:
целевая аудитория, конкуренты, размер рынка, ключевые инсайты.
Работает параллельно с product-analyst, strategist, financier.

Инструкции: `skills/business/02-target-audience.md`, `skills/business/03-competitive-analysis.md`, `skills/business/05-market-size.md`, `skills/business/13-market-insights.md`

---

## 2. Входящие файлы

| Файл | Откуда | Назначение |
|---|---|---|
| `.ai/chats/business/cross-brief.md` | product-manager | первичный контекст задачи |
| `.ai/chats/business/market-analyst/experience.md` | сам агент | накопленный опыт |
| `.ai/chats/business/market-analyst/qna.json` | пользователь (через UI) | ответы на уточняющие вопросы |

---

## 3. Процесс работы

```
1. Прочитать cross-brief.md и experience.md

2. Оценить: достаточно ли данных?
   — Если нет → вопросы в qna.json → ждать ответов
   — Если да → перейти к анализу
   Примечание: для закрытых personal tools большинство секций сворачиваются
   в минимальный конкурентный анализ UX-ориентиров.

3. Выполнить анализ по четырём инструкциям:

   [02-target-audience] — см. skills/business/02-target-audience.md
   Описать сегменты, портреты пользователей (jobs-to-be-done, боли, мотивы),
   ранних адопторов.

   [03-competitive-analysis] — см. skills/business/03-competitive-analysis.md
   Прямые и косвенные конкуренты, сравнение по ключевым параметрам,
   незакрытые ниши.

   [05-market-size] — см. skills/business/05-market-size.md
   TAM/SAM/SOM (для коммерческих продуктов), динамика рынка.
   Для personal tools: пропустить или обозначить N/A.

   [13-market-insights] — см. skills/business/13-market-insights.md
   Ключевые выводы, риски, возможности, рекомендации по позиционированию.

4. Написать report.md (структура: аудитория → конкуренты → рынок → инсайты)

5. Обновить experience.md
```

---

## 4. Исходящие файлы

| Файл | Куда | Routing |
|---|---|---|
| `.ai/chats/business/market-analyst/qna.json` | UI → пользователь | вопросы агента |
| `.ai/chats/business/market-analyst/report.md` | product-manager | исходный файл |
| `→ .ai/chats/business/product-manager/reports/market-analyst.md` | product-manager | Harvester копирует автоматически |

---

## 5. Обновление experience.md

```
## {task-id} | {дата}
Тип рынка: {B2C/B2B/personal}. Конкуренты найдены: {N}.
Паттерн: {если что-то важное}
```

---

## 6. Статус завершения

После записи report.md:
```json
pipeline-state.json → agents["market-analyst"] = "done"
```
