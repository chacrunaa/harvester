# TASK3 — Полный пакет бизнес-анализа проекта

## Что ты собираешь и зачем

Ты собираешь **полный пакет бизнес-анализа** из 13–14 документов для проекта, материалы которого лежат в `data/input/`.

Пакет нужен команде и заказчику для принятия решений о продукте, MVP и бизнес-стратегии.
Каждый документ пакета — самостоятельная рабочая единица, которую можно взять и использовать:
Product Brief на встречу с инвестором, юнит-экономику для финансового планирования, CustDev-план для проведения интервью.

**Перед запуском прочитай:**
1. `data/output/00-business-context.md` — **сначала этот файл**: это сводный «паспорт проекта», созданный в TASK2. Содержит все ключевые факты, KPI, конверсии, конкурентов и открытые гипотезы в одном месте.
2. Все файлы из `data/input/` — понять суть продукта, функциональность, архитектуру, бизнес-контекст
3. Все файлы из `data/info/` — структурированные данные клиента: конверсии, цены, KPI, риски, пробелы

Из этих материалов выпиши ключевые параметры проекта и используй их во ВСЕХ последующих документах:
ICP-сегменты, конверсии воронки, ценовые якоря, KPI на 6 и 12 мес, конкурентов, критичные зависимости, дату пилота и MVP.

---

## СТОП — ПРОЧТИ ПЕРЕД ЗАПУСКОМ

**Выходной файл каждого шага — это документ с реальным написанным содержанием.**

Не создавай README. Не создавай заглушки. Не пиши «данные появятся после выполнения».
Файл `README.md` в папке шага — это НЕ результат. Если ты создаёшь или обновляешь README — ты делаешь неправильно.

**Если ты видишь в папке `data/output/NN-название/` только `README.md` — папка пустая. Работа не выполнена.**

Пример правильного результата шага 1:
- `data/output/01-product-brief/01-product-brief.md` — файл с реальным содержанием по структуре инструкции

Пример НЕПРАВИЛЬНОГО результата:
- `data/output/01-product-brief/README.md` — это заглушка, не результат

---

## Сколько файлов создавать на каждый шаг

**На каждый шаг создай столько файлов, сколько нужно для полного раскрытия темы.**

Минимум — один файл с именем `NN-название.md` в папке шага.
Если содержание не умещается или логически делится — создавай дополнительные файлы.

Примеры допустимой разбивки:
- `data/output/08-unit-economics/08-unit-economics.md` — основной расчёт
- `data/output/08-unit-economics/08-unit-economics-scenarios.md` — таблицы по сценариям
- `data/output/10-financial-model/10-financial-model.md` — модель и сводка
- `data/output/10-financial-model/10-financial-model-pl.md` — P&L 12 мес
- `data/output/12-custdev-plan/12-custdev-plan.md` — план и гипотезы
- `data/output/12-custdev-plan/12-custdev-plan-script-icp1.md` — скрипт интервью ICP-1
- `data/output/12-custdev-plan/12-custdev-plan-script-icp2.md` — скрипт интервью ICP-2

Количество файлов определяешь сам исходя из объёма и полноты содержания.

---

## Входные данные проекта — прочитать ВСЕ перед запуском

```
data/input/           ← Все исходные материалы по продукту
  intro.md            ← Введение: суть продукта, проблема, решение
  business/           ← Бизнес-документы: бизнес-модель, конкуренты, процессы
  features/           ← Описание функциональности
  architecture/       ← Архитектурные документы (стек, MVP, пилот)
  requirements/       ← Функциональные и нефункциональные требования
  ui/                 ← Описание интерфейсов (если есть)

data/info/            ← КРИТИЧНО: структурированные данные клиента
  (файлы из TASK2 — конверсии, KPI, ценообразование, риски, пробелы)
```

**Перед выполнением шагов прочитать все файлы и зафиксировать:**

| Параметр | Из каких файлов брать |
|---------|----------------------|
| Название и категория продукта | data/input/intro.md |
| ICP-сегменты (кто главный покупатель) | data/info/ |
| Конверсия visit→signup | data/info/ |
| Конверсия signup→payment | data/info/ |
| Upsell / attach-rate | data/info/ |
| Ценовые якоря (базовая цена, upsell-цена) | data/info/ |
| ФОТ и OPEX | data/info/ |
| KPI 6 мес и 12 мес | data/info/ |
| Конкуренты | data/info/ + data/input/business/ |
| Критичные технические зависимости | data/info/ + data/input/ |
| Дата пилота и MVP | data/info/ + data/input/ |
| Целевая география | data/info/ |

Всё что нашёл — это **факты** (использовать напрямую).
Всё что не нашёл — строить как **гипотезу** с явным `[гипотеза]` и обоснованием.

---

## Порядок выполнения шагов

```
Шаг 1 (Бриф)
    │
    ├──→ Шаг 2 (ЦА)
    │       │
    │       ├──→ Шаг 3 (Конкуренты) ──→ Шаг 7 (УТП)
    │       │
    │       ├──→ Шаг 4 (БФТ) ──→ Шаг 11 (MVP) ──→ Шаг 12 (CustDev)
    │       │
    │       └──→ Шаг 5 (Рынок) ──→ Шаг 6 (Бизнес-модель) ──→ Шаг 8 (Юнит-экономика)
    │                                                                  │
    │                                                        Шаг 9 (Метрики)
    │                                                        Шаг 10 (Финмодель)
    │
    └──→ Шаг 13 (Инсайты) — независимый, можно параллельно со Шагами 2–3
    └──→ Шаг 14 (Python) — только при наличии CSV-данных в data/input/
```

---

## Таблица шагов — точные пути

Что ожидается в каждой папке — смотри README внутри папки шага.

| Шаг | Инструкция | Входные данные | Создать файл(ы) в | Ожидаемый результат |
|:---:|-----------|----------------|-------------------|---------------------|
| 1 | `instructions/main/01-product-brief.md` | data/input/intro.md, data/input/business/*, data/info/* | `data/output/01-product-brief/` | [README](../data/output/01-product-brief/README.md) |
| 2 | `instructions/main/02-target-audience.md` | data/output/01-product-brief/*, data/input/business/workflows.md, data/info/* | `data/output/02-target-audience/` | [README](../data/output/02-target-audience/README.md) |
| 3 | `instructions/main/03-competitive-analysis.md` | data/output/01-product-brief/*, data/output/02-target-audience/*, data/input/business/competitive-analysis.md, data/info/* | `data/output/03-competitive-analysis/` | [README](../data/output/03-competitive-analysis/README.md) |
| 4 | `instructions/main/04-bft.md` | data/output/01-product-brief/*, data/output/02-target-audience/*, data/output/03-competitive-analysis/*, data/input/features/*, data/input/architecture/*, data/input/requirements/* | `data/output/04-bft/` | [README](../data/output/04-bft/README.md) |
| 5 | `instructions/main/05-market-size.md` | data/output/01-product-brief/*, data/output/02-target-audience/*, data/info/* | `data/output/05-market-size/` | [README](../data/output/05-market-size/README.md) |
| 6 | `instructions/main/06-business-model.md` | data/output/01-product-brief/*, data/output/02-target-audience/*, data/output/03-competitive-analysis/*, data/output/05-market-size/*, data/input/business/business-model.md | `data/output/06-business-model/` | [README](../data/output/06-business-model/README.md) |
| 7 | `instructions/main/07-value-proposition.md` | data/output/01-product-brief/*, data/output/02-target-audience/*, data/output/03-competitive-analysis/* | `data/output/07-value-proposition/` | [README](../data/output/07-value-proposition/README.md) |
| 8 | `instructions/main/08-unit-economics.md` | data/output/05-market-size/*, data/output/06-business-model/*, data/info/* | `data/output/08-unit-economics/` | [README](../data/output/08-unit-economics/README.md) |
| 9 | `instructions/main/09-product-metrics.md` | data/output/01-product-brief/*, data/output/06-business-model/*, data/output/08-unit-economics/*, data/info/* | `data/output/09-product-metrics/` | [README](../data/output/09-product-metrics/README.md) |
| 10 | `instructions/main/10-financial-model.md` | data/output/05-market-size/*, data/output/06-business-model/*, data/output/08-unit-economics/*, data/output/09-product-metrics/*, data/info/* | `data/output/10-financial-model/` | [README](../data/output/10-financial-model/README.md) |
| 11 | `instructions/main/11-mvp-definition.md` | data/output/02-target-audience/*, data/output/04-bft/*, data/output/08-unit-economics/*, data/input/architecture/mvp.md, data/input/requirements/mvp-scope.md | `data/output/11-mvp-definition/` | [README](../data/output/11-mvp-definition/README.md) |
| 12 | `instructions/main/12-custdev-plan.md` | data/output/02-target-audience/*, data/output/11-mvp-definition/*, data/info/* | `data/output/12-custdev-plan/` | [README](../data/output/12-custdev-plan/README.md) |
| 13 | `instructions/main/13-market-insights.md` | data/output/01-product-brief/*, data/output/03-competitive-analysis/*, data/info/*, интернет (если доступен) | `data/output/13-market-insights/` | [README](../data/output/13-market-insights/README.md) |
| 14 | `instructions/main/14-python-pipeline.md` | data/output/08-unit-economics/*, data/output/09-product-metrics/*, data/output/10-financial-model/*, CSV-данные из data/input/ | `data/output/14-python-pipeline/` | [README](../data/output/14-python-pipeline/README.md) |

**Главный файл каждого шага называется:** `NN-название.md`
Дополнительные файлы — по смыслу содержания.

---

## Обязательные требования к каждому документу

### Содержание

- **Все разделы из инструкции** — заполнены без исключений
- **Все таблицы и выводы заполнены содержательно** — числа использовать там, где они реально есть или обоснованно выведены
- **Все расчёты показаны явно** — формула + подстановка чисел + результат
- **Данные проекта использованы** — конверсии, цены, KPI из `data/info/`
- **Конкуренты названы по имени** — из `data/info/` и `data/input/business/`
- Если данных нет — писать конкретную гипотезу с обоснованием и `[гипотеза]`

### Запрещено

- Создавать README вместо содержательного документа
- Писать «данные будут добавлены позже»
- Использовать abstract bullet-list вместо заполненных таблиц
- Пропускать разделы «потому что нет данных»
- Сокращать документ ради экономии токенов

---

## Проверка перед переходом к следующему шагу

- [ ] Файл создан с именем `NN-название.md` (не README.md)
- [ ] Документ содержит все разделы из соответствующей инструкции
- [ ] Нет пустых критичных разделов и незаполненных таблиц без пояснения
- [ ] Реальные данные проекта использованы (не придуманы)
- [ ] Качество важнее объёма: документ достаточен для практического использования
- [ ] Расчёты показаны с числами (не только формулы)

Если документ не прошёл проверку → выполнить шаг заново.

---

## Definition of Done

Задание выполнено, когда:

- [ ] В `data/output/` есть минимум 13 содержательных документов (шаги 1–13)
- [ ] Каждый документ — файл с реальным содержанием, а не README
- [ ] Каждый документ соответствует всем требованиям выше
- [ ] Шаг 14 — выполнен (если есть CSV-данные) или документирована причина пропуска
- [ ] Все документы используют реальные данные проекта из `data/info/`
