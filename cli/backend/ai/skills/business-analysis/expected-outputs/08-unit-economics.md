# 08-unit-economics — Юнит-экономика

Шаг 8 пайплайна TASK3. Расчётный документ: при каких условиях бизнес зарабатывает, а при каких — нет.

**Инструкция:** [`instructions/main/08-unit-economics.md`](../../instructions/main/08-unit-economics.md)  
**Задача:** [`tasks/TASK3.md`](../../tasks/TASK3.md)

---

## Ожидаемые файлы

| Файл | Назначение | Объём |
|------|-----------|-------|
| `08-unit-economics.md` | Основной документ (все 10 разделов) | ≥200 строк |
| `08-unit-economics-scenarios.md` | Таблицы Bear / Base / Bull, если объёмные | опционально |
| `08-unit-economics-breakeven.md` | Break-even и анализ чувствительности | опционально |

**Файл с результатом называется `08-unit-economics.md`, не README.md.**

---

## Разделы документа

### 1. Таблица допущений (все входные параметры, 3 сценария)

| Параметр | Bear | Base | Bull | Источник |
|---------|:----:|:----:|:----:|---------|
| Базовая цена юнита (<currency>) | (Bear) | (из data/info/) | (Bull) | Данные клиента |
| Цена upsell (<currency>) | | (из data/info/) | | Данные клиента |
| Attach-rate upsell (%) | | (из data/info/) | | Данные клиента |
| Комиссия платёжной системы (%) | (%) | (%) | (%) | `[гипотеза]` |
| CAC (<currency>) | | (из data/info/) | | Данные клиента |
| CR visit→signup | | (из data/info/) | | Данные клиента |
| CR signup→payment | | (из data/info/) | | Данные клиента |
| Infra на заказ (<currency>) | | | | `[гипотеза]` из OPEX |
| Retention (повторная покупка, %) | | | | `[гипотеза]` |

### 2. ARPU — расчёт явно, пошагово для Base

```
Шаг 1: Базовая цена = X <currency> (из data/info/)
Шаг 2: Upsell = attach-rate × upsell_price = Y% × Z <currency> = W <currency>
Шаг 3: Gross Revenue = X + W = N <currency>
Шаг 4: Комиссия = N × 3% [гипотеза] = C <currency>
Шаг 5: Net Revenue/Order = N − C = [итого] <currency>
```

| Параметр | Bear | Base | Bull |
|---------|-----:|-----:|-----:|
| Gross Revenue/Order (<currency>) | | | |
| Комиссия (<currency>) | | | |
| **Net Revenue/Order (<currency>)** | | | |

### 3. Variable Costs — переменные затраты на заказ

```
Infra = [месячный OPEX infra] / [прогноз заказов/мес] = X <currency>/заказ [гипотеза]
Upsell ops = attach-rate × стоимость/заявку = Y <currency>
Комиссия = [из раздела 2]
Total Variable Cost = X + Y + комиссия
```

### 4. Contribution Margin

```
Net Revenue/Order:   [из раздела 2]
Variable Cost/Order: [из раздела 3]
────────────────────────────────────
CM:                  Net − Variable
CM%:                 CM / Net = X%
```

| Параметр | Bear | Base | Bull |
|---------|-----:|-----:|-----:|
| **Contribution Margin (<currency>)** | | | |
| **CM%** | | | |

### 5. CAC и Unit Margin

```
MVP: CAC = X <currency> (из data/info/)
Unit Margin = CM − CAC = Y <currency>

Post-MVP (с платным привлечением [гипотеза]):
[Каналы из data/info/] CAC ≈ Z <currency>
Unit Margin post-MVP = CM − blended_CAC
```

### 6. LTV — двумя методами

**Метод 1 (простой):**
```
LTV = Net Revenue/Order × avg_purchases
avg_purchases = 1 + retention% × коэффициент
LTV = [Net Revenue] × [avg_purchases] = [итого <currency>] (Base)
```

**Метод 2 (когортный с discount rate):**
```
LTV = ARPU × Σ(retention_n × discount_factor_n)
```

| Параметр | Bear | Base | Bull |
|---------|-----:|-----:|-----:|
| Avg purchases (12 мес) | | | |
| **LTV простой (<currency>)** | | | |
| **LTV когортный (<currency>)** | | | |

### 7. LTV/CAC Ratio

| Сценарий | LTV (<currency>) | CAC (<currency>) | **LTV/CAC** |
|---------|:----------:|:---------:|:-----------:|
| Bear | | | |
| Base | | | |
| Bull | | | |

Интерпретация: <1x = убыточен, 1–3x = приемлемо, **3x+** = здоровый, 5x+ = отличный.

### 8. Payback Period

```
Payback = CAC / CM = [N заказов] → [M месяцев при прогнозе]
```

### 9. Break-even (таблица: 3 сценария OPEX)

```
Fixed OPEX (MVP) = X <currency>/мес (из 06-business-model)
Break-even = X / CM = Y заказов/мес
```

| Сценарий | Monthly OPEX (<currency>) | CM/Order (<currency>) | Break-even заказов/мес |
|---------|:-------------------:|:---------------:|:----------------------:|
| MVP (ФОТ = 0) | (из 06) | (из р. 4) | (рассчитать) |
| Base | (из 06) | | |
| Стресс (рыночный ФОТ `[гипотеза]`) | +X <currency> | | |

### 10. Сценарный анализ P&L (5 точек объёма)

| Заказов/мес | Net Revenue | Variable Costs | Contribution | Fixed OPEX | EBITDA |
|:-----------:|------------:|:--------------:|:-----------:|:---------:|:------:|
| [N1 — старт] | | | | (из 06) | |
| [N2] | | | | | |
| [KPI-цель из data/info/] | | | | | |
| [N4] | | | | | |
| [N5 — масштаб] | | | | | |

---

## Минимальные требования

- [ ] Документ ≥200 строк markdown
- [ ] Все 10 разделов с числами — нет пустых ячеек
- [ ] Каждый расчёт показан явно: формула + числа + результат
- [ ] 3 сценария (Bear / Base / Bull) для ключевых показателей
- [ ] LTV рассчитан двумя методами
- [ ] Break-even таблица с 3 сценариями OPEX
- [ ] Конверсии и цены из `data/info/`, не выдуманы
