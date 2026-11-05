# Система документирования — .ai/rules/docs/

## Что это

Инструкции для генерации **читаемой документации** в `docs/{task-id}/`.

Каждая инструкция описывает:
- Роль AI-агента (как должен думать и писать)
- Теоретическую базу (фреймворки, термины, методологии)
- Конкретную задачу (что должно быть в документе)
- Формат вывода (структура, объём, критерии качества)

Документы пишутся **простым языком для начинающего бизнес-аналитика**: без жаргона, с объяснением терминов, с примерами, подробно.

---

## Маппинг: агент → инструкции → docs-файл

| Агент | Инструкции | Выходной файл в docs/ |
|---|---|---|
| `business/product-manager` | [01](./01-product-brief.md) + [11](./11-mvp-definition.md) | `docs/{task-id}/business/brief.md` |
| `business/product-analyst` | [02](./02-target-audience.md) + [07](./07-value-proposition.md) + [09](./09-product-metrics.md) + [12](./12-custdev-plan.md) | `docs/{task-id}/business/product-analyst.md` |
| `business/market-analyst` | [03](./03-competitive-analysis.md) + [05](./05-market-size.md) + [13](./13-market-insights.md) | `docs/{task-id}/business/market-analyst.md` |
| `business/strategist` | [06](./06-business-model.md) + [07](./07-value-proposition.md) | `docs/{task-id}/business/strategist.md` |
| `business/financier` | [08](./08-unit-economics.md) + [10](./10-financial-model.md) | `docs/{task-id}/business/financier.md` |
| `systemic/owner` | [04](./04-bft.md) | `docs/{task-id}/systemic/spec.md` |
| `systemic/architect` | [15](./15-architecture.md) | `docs/{task-id}/systemic/architecture.md` |
| `systemic/analyst` | [16](./16-api-spec.md) | `docs/{task-id}/systemic/api-spec.md` |
| `development/backend` | [17](./17-backend.md) | `docs/{task-id}/development/backend.md` |
| `development/frontend` | [18](./18-frontend.md) | `docs/{task-id}/development/frontend.md` |
| `development/reviewers` | [19](./19-code-review.md) | `docs/{task-id}/development/review.md` |
| `testing/qa` | [20](./20-qa-testing.md) | `docs/{task-id}/testing/qa.md` |
| `testing/penetration` | [21](./21-security.md) | `docs/{task-id}/testing/security.md` |

---

## Рекомендуемый порядок чтения документации

```
business/
  brief.md              ← начни отсюда: что делаем и для кого
  product-analyst.md    ← ЦА, ценностное предложение, метрики
  market-analyst.md     ← рынок, конкуренты, инсайты
  strategist.md         ← бизнес-модель, стратегия
  financier.md          ← юнит-экономика, финансовая модель

systemic/
  spec.md               ← функциональные требования (для разработчиков)
  architecture.md       ← архитектура системы
  api-spec.md           ← API и модель данных

development/
  backend.md / frontend.md / review.md

testing/
  qa.md / security.md
```

---

## Правила написания docs-документов

Все документы в `docs/` должны:

1. **Быть понятны новичку** — объяснять каждый термин прямо в тексте
2. **Быть подробными** — не сокращать, расписывать каждый пункт
3. **Содержать "Почему это важно"** — практическая ценность каждого раздела
4. **Использовать примеры и аналогии** — там где помогает понять
5. **Заканчиваться "Ключевыми выводами"** — 3-5 пунктов самого важного
6. **Не копировать технический текст дословно** — перефразировать и объяснять
7. **Тон: дружелюбный, наставнический** — как опытный коллега объясняет новичку

---

## Инструкции

| # | Файл | Что генерирует |
|---|---|---|
| 01 | [01-product-brief.md](./01-product-brief.md) | Бриф продукта (Product Vision, проблема, решение, метрики) |
| 02 | [02-target-audience.md](./02-target-audience.md) | Целевая аудитория (JTBD, сегменты, персоны) |
| 03 | [03-competitive-analysis.md](./03-competitive-analysis.md) | Конкурентный анализ (SWOT, карта конкурентов) |
| 04 | [04-bft.md](./04-bft.md) | Бизнес-функциональные требования (MoSCoW, ICE/RICE) |
| 05 | [05-market-size.md](./05-market-size.md) | Расчёт рынка (TAM/SAM/SOM) |
| 06 | [06-business-model.md](./06-business-model.md) | Бизнес-модель (Canvas Остервальдера) |
| 07 | [07-value-proposition.md](./07-value-proposition.md) | Ценностное предложение (УТП, Value Proposition Canvas) |
| 08 | [08-unit-economics.md](./08-unit-economics.md) | Юнит-экономика (CAC, LTV, ARPU) |
| 09 | [09-product-metrics.md](./09-product-metrics.md) | Метрики продукта (NSM, KPI, дерево метрик) |
| 10 | [10-financial-model.md](./10-financial-model.md) | Финансовая модель (P&L, CashFlow, сценарии) |
| 11 | [11-mvp-definition.md](./11-mvp-definition.md) | Определение MVP (гипотезы, HADI, скоп) |
| 12 | [12-custdev-plan.md](./12-custdev-plan.md) | CustDev план (сценарии интервью, гипотезы) |
| 13 | [13-market-insights.md](./13-market-insights.md) | Рыночные инсайты (тренды, точки роста) |
| 15 | [15-architecture.md](./15-architecture.md) | Архитектура системы (компоненты, взаимодействие, технологии) |
| 16 | [16-api-spec.md](./16-api-spec.md) | API и модель данных (endpoints, сущности, потоки данных) |
| 17 | [17-backend.md](./17-backend.md) | Backend: что реализовано (функции, интеграции, надёжность) |
| 18 | [18-frontend.md](./18-frontend.md) | Frontend: что реализовано (экраны, UX, адаптивность) |
| 19 | [19-code-review.md](./19-code-review.md) | Ревью кода (находки, критичность, рекомендации) |
| 20 | [20-qa-testing.md](./20-qa-testing.md) | Результаты тестирования (баги, покрытие, готовность к запуску) |
| 21 | [21-security.md](./21-security.md) | Анализ безопасности (уязвимости, риски, план устранения) |
