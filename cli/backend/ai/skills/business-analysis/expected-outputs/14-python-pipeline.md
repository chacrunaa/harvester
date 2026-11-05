# 14-python-pipeline — Python-пайплайн для анализа данных

Шаг 14 пайплайна TASK3. **Выполняется только при наличии реальных CSV/Excel-данных.**  
Если данных нет — документируется структура данных для сбора с первого дня + шаблоны скриптов.

**Инструкция:** [`instructions/main/14-python-pipeline.md`](../../instructions/main/14-python-pipeline.md)  
**Задача:** [`tasks/TASK3.md`](../../tasks/TASK3.md)

---

## Ожидаемые файлы

| Файл | Назначение |
|------|-----------|
| `14-python-pipeline.md` | Документация: схемы данных, инструкция по запуску, что считает каждый скрипт |
| `01_eda.py` | EDA: базовая статистика, распределения, аномалии |
| `02_business_metrics.py` | ARPU, CAC, LTV, retention из реальных данных |
| `03_cohort_analysis.py` | Когортный анализ (retention по когортам) |
| `04_funnel_analysis.py` | Воронка AARRR с реальными конверсиями |
| `05_unit_economics.py` | Юнит-экономика план vs факт |
| `requirements.txt` | Зависимости Python |

**Если данных нет — скрипты содержат синтетические данные для тестирования и документирования структуры.**

---

## Содержание 14-python-pipeline.md

### 1. Требования к окружению

```bash
pip install -r requirements.txt
```

`requirements.txt`:
```
pandas>=2.0.0
numpy>=1.24.0
matplotlib>=3.7.0
seaborn>=0.12.0
plotly>=5.15.0
```

### 2. Структура входных данных (схемы CSV — адаптировать под продукт)

**transactions.csv** — транзакции:
```csv
transaction_id, user_id, created_at,
[product-specific: тип юнита из data/input/features/],
base_price, upsell_taken, upsell_price,
payment_status, payment_provider, currency
```

**users.csv** — пользователи:
```csv
user_id, registered_at,
[product-specific: сегмент из data/output/02-target-audience/],
first_purchase_at, total_purchases, total_spent
```

**events.csv** — события пользовательского пути:
```csv
event_id, user_id, session_id, event_type, created_at, properties
(event_types из data/input/business/workflows.md: page_view, signup, ...)
```

### 3. Что считает каждый скрипт

**01_eda.py:**
- Загружает все CSV
- Выводит shape, dtypes, null counts
- Строит распределения ключевых переменных (цены, upsell доля)
- Находит аномалии (отрицательные суммы, дубликаты)
- Сохраняет графики в `output/eda/`

**02_business_metrics.py:**
- ARPU = (base_price + upsell_revenue) / total_orders
- CAC = marketing_spend / new_users (если есть marketing_spend.csv)
- LTV по когортам: ARPU × avg_purchases × retention
- Retention M1, M3, M6 из когортного анализа

```python
def calculate_arpu(transactions):
    total_revenue = transactions["base_price"].sum() + transactions["upsell_price"].fillna(0).sum()
    total_orders = len(transactions)
    return total_revenue / total_orders
```

**03_cohort_analysis.py:**
- Когортный анализ по месяцу первой покупки
- Матрица retention: строка = когорта, столбец = месяц после первой покупки
- Визуализация тепловой карты

**04_funnel_analysis.py:**
- AARRR: посетители → регистрации → заказы → повторные → рефералы
- Конверсии на каждом шаге (план vs факт)
- Сравнение с целевыми значениями из data/info/

**05_unit_economics.py:**
- Расчёт план vs факт для ARPU, CM, Break-even
- Сравнение с таблицей допущений из 08-unit-economics.md
- P&L факт по месяцам (если есть данные)

### 4. Как запускать

```bash
# Запуск всех скриптов последовательно
python 01_eda.py
python 02_business_metrics.py
python 03_cohort_analysis.py
python 04_funnel_analysis.py
python 05_unit_economics.py

# Результаты в папке output/
```

### 5. Что делать если данных нет

Если CSV не предоставлены:
1. Скрипты содержат синтетические данные, генерируемые автоматически
2. Структура данных задокументирована — начать сбор с первого дня MVP
3. Флаг `USE_SYNTHETIC = True` в начале каждого скрипта — переключить на `False` при появлении реальных данных

---

## Минимальные требования

- [ ] `14-python-pipeline.md` — документация ≥60 строк
- [ ] Все 5 скриптов созданы и запускаются (`python script.py` без ошибок)
- [ ] `requirements.txt` создан
- [ ] Схемы данных адаптированы под конкретный продукт (не шаблонные поля)
- [ ] Если данных нет — явно указано в документе, синтетические данные есть
- [ ] Скрипты сохраняют результаты в `output/` (создаётся автоматически)
