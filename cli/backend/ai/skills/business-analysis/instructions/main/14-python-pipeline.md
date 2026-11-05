# Инструкция 14 — Python-пайплайн для анализа данных

Бизнес-модель, сущности данных, воронку событий и сегменты пользователей определить из `data/input/` (features, business/workflows.md) и `data/output/02-target-audience/`. Схемы CSV адаптировать под конкретный продукт — не использовать шаблонные поля.

## Выходные файлы

**Главный файл:** `data/output/14-python-pipeline/14-python-pipeline.md` — документация и инструкция по запуску.
**Python-скрипты:** `data/output/14-python-pipeline/scripts/`.

Структура скриптов (создать отдельные .py файлы, не встраивать в markdown):
- `01_eda.py` — EDA и базовая статистика
- `02_business_metrics.py` — ARPU, CAC, LTV, retention
- `03_cohort_analysis.py` — когортный анализ
- `04_funnel_analysis.py` — воронка AARRR
- `05_unit_economics.py` — юнит-экономика план vs факт
- `requirements.txt` — зависимости

**НЕ создавай README.md как единственный файл — создавай реальные Python-скрипты.**

## Твоя роль

Ты — data analyst / data engineer с опытом в product analytics и финансовом анализе. Твоя задача — написать готовые Python-скрипты для расчёта бизнес-метрик [Название продукта] на основе реальных данных. Скрипты должны запускаться командой `python script.py` без дополнительной настройки (кроме установки зависимостей).

## Условие запуска

**Этот шаг выполняется только при наличии реальных данных в CSV/Excel.**

Если данных нет — написать в документе:
1. Какие данные нужно собирать с первого дня после запуска MVP
2. Структуру таблиц (схема данных), адаптированную под продукт
3. Шаблоны скриптов с синтетическими данными для тестирования

## Входные файлы

- `data/output/08-unit-economics/08-unit-economics.md`
- `data/output/09-product-metrics/09-product-metrics.md`
- `data/output/10-financial-model/10-financial-model.md`
- `data/input/` — для определения схем данных под конкретный продукт

## Ключевые данные (определить перед написанием скриптов)

Перед написанием прочитать `data/input/` и определить:
- Какие сущности создаёт продукт (транзакции, заявки, проекты, документы — в зависимости от бизнес-модели)
- Какие поля специфичны для данного продукта (из `data/input/features/` или `data/input/business/`)
- Какой upsell есть и как он фиксируется в данных
- Какие события пользовательского пути нужно трекать (из `data/input/business/workflows.md`)

## Ожидаемые данные (структура CSV — адаптировать под конкретный продукт)

**⚠️ Схемы ниже — шаблонные. Поля, помеченные `[product-specific]`, определить из `data/input/`.**

### transactions.csv
```csv
transaction_id, user_id, created_at,
[product-specific: тип основного юнита из data/input/features/],
base_price, upsell_taken, upsell_price,
payment_status, payment_provider, currency
```

### users.csv
```csv
user_id, registered_at,
[product-specific: сегмент пользователя из data/output/02-target-audience/],
first_purchase_at, total_purchases, total_spent
```

### events.csv
```csv
event_id, user_id, session_id, event_type, created_at, properties
(event_types определить из data/input/business/workflows.md:
 page_view, signup, [шаги воронки из workflows.md], payment_success, [финальное действие])
```

### marketing_spend.csv (если есть)
```csv
date, channel, spend, clicks, impressions
```

## Структура выходного документа

### 1. Требования к окружению

```bash
pip install pandas numpy matplotlib seaborn plotly
```

Создать файл `requirements.txt`:
```
pandas>=2.0.0
numpy>=1.24.0
matplotlib>=3.7.0
seaborn>=0.12.0
plotly>=5.15.0
```

### 2. Скрипт 1: EDA (Exploratory Data Analysis)

Файл: `data/output/14-python-pipeline/scripts/01_eda.py`

Скрипт должен:
1. Загрузить все CSV из `data/input/data/` (или указанной директории)
2. Вывести базовую статистику (shape, dtypes, null counts)
3. Построить распределения ключевых числовых переменных
4. Найти и отметить аномалии (отрицательные суммы, дубликаты)
5. Сохранить графики в `data/output/14-python-pipeline/output/eda/`

```python
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path

DATA_DIR = Path("data/input/data")
OUTPUT_DIR = Path("data/output/14-python-pipeline/output/eda")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

def load_data():
    """Загрузка всех CSV файлов."""
    try:
        transactions = pd.read_csv(DATA_DIR / "transactions.csv", parse_dates=["created_at"])
        users = pd.read_csv(DATA_DIR / "users.csv", parse_dates=["registered_at", "first_purchase_at"])
        events = pd.read_csv(DATA_DIR / "events.csv", parse_dates=["created_at"])
        return transactions, users, events
    except FileNotFoundError as e:
        print(f"Файл не найден: {e}. Используйте синтетические данные для тестирования.")
        raise

def basic_stats(df, name):
    """Базовая статистика датафрейма."""
    print(f"\n=== {name} ===")
    print(f"Shape: {df.shape}")
    print(f"Null counts:\n{df.isnull().sum()}")
    print(f"Dtypes:\n{df.dtypes}")
    print(f"Sample:\n{df.head(3)}")

def plot_revenue_distribution(transactions):
    """Распределение выручки."""
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))

    sns.histplot(transactions["base_price"], bins=20, ax=axes[0])
    axes[0].set_title("Распределение базовой цены (<currency>)")
    axes[0].set_xlabel("Цена")

    upsell_pct = transactions["upsell_taken"].value_counts(normalize=True) * 100
    axes[1].bar(["Без upsell", "С upsell"], upsell_pct.values)
    axes[1].set_title(f"Доля заказов с upsell\n({upsell_pct.get(True, 0):.1f}%)")
    axes[1].set_ylabel("%")

    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / "revenue_distribution.png", dpi=150)
    plt.close()

def plot_transactions_over_time(transactions):
    """Динамика транзакций по времени."""
    monthly = transactions.resample("ME", on="created_at").agg(
        orders=("transaction_id", "count"),
        revenue=("base_price", "sum")
    ).reset_index()

    fig, ax1 = plt.subplots(figsize=(12, 5))
    ax2 = ax1.twinx()

    ax1.bar(monthly["created_at"], monthly["orders"], alpha=0.6, label="Заказов/мес", color="steelblue")
    ax2.plot(monthly["created_at"], monthly["revenue"], color="red", linewidth=2, label="Выручка")

    ax1.set_xlabel("Месяц")
    ax1.set_ylabel("Заказов", color="steelblue")
    ax2.set_ylabel("Выручка", color="red")
    ax1.set_title("Динамика заказов и выручки по месяцам")

    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / "transactions_over_time.png", dpi=150)
    plt.close()

if __name__ == "__main__":
    transactions, users, events = load_data()
    basic_stats(transactions, "transactions")
    basic_stats(users, "users")
    basic_stats(events, "events")
    plot_revenue_distribution(transactions)
    plot_transactions_over_time(transactions)
    print(f"\nГрафики сохранены в {OUTPUT_DIR}")
```

### 3. Скрипт 2: Business Metrics (ARPU, CAC, Retention)

Файл: `data/output/14-python-pipeline/scripts/02_business_metrics.py`

Скрипт должен рассчитывать:

```python
import pandas as pd
import numpy as np
from pathlib import Path

DATA_DIR = Path("data/input/data")
OUTPUT_DIR = Path("data/output/14-python-pipeline/output/metrics")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

def calculate_arpu(transactions):
    """ARPU — средняя выручка на заказ."""
    total_revenue = (
        transactions["base_price"] +
        transactions["upsell_price"].fillna(0)
    )
    arpu = total_revenue.mean()
    median_revenue = total_revenue.median()
    upsell_rate = transactions["upsell_taken"].mean() * 100

    print(f"\n=== ARPU ===")
    print(f"Средняя выручка/заказ: {arpu:.0f}")
    print(f"Медианная выручка/заказ: {median_revenue:.0f}")
    print(f"Attach-rate upsell: {upsell_rate:.1f}%")
    return arpu

def calculate_funnel(events):
    """AARRR воронка — шаги определены из workflows.md."""
    # Адаптировать event_types под конкретный продукт
    funnel_steps = [
        "page_view", "signup", "checkout_start",
        "payment_success", "key_action_complete"
    ]
    funnel_labels = [
        "Посетители", "Регистрации", "Начали оформление",
        "Оплатили", "Завершили ключевое действие"
    ]

    funnel_counts = []
    for step in funnel_steps:
        count = events[events["event_type"] == step]["user_id"].nunique()
        funnel_counts.append(count)

    print(f"\n=== AARRR Воронка ===")
    for label, count, prev in zip(funnel_labels, funnel_counts, [None] + funnel_counts):
        cr = f" (CR: {count/prev*100:.1f}%)" if prev else ""
        print(f"{label}: {count:,}{cr}")

    return dict(zip(funnel_labels, funnel_counts))

def calculate_retention(transactions):
    """Retention — возврат пользователей."""
    user_purchases = (
        transactions
        .sort_values("created_at")
        .groupby("user_id")["created_at"]
        .apply(list)
        .reset_index()
    )

    user_purchases["first_purchase"] = user_purchases["created_at"].apply(lambda x: x[0])
    user_purchases["repeat_in_90d"] = user_purchases.apply(
        lambda row: any(
            (d - row["first_purchase"]).days <= 90 and d != row["first_purchase"]
            for d in row["created_at"]
        ),
        axis=1
    )

    retention_90d = user_purchases["repeat_in_90d"].mean() * 100
    print(f"\n=== Retention ===")
    print(f"Retention 90 дней (repeat purchase): {retention_90d:.1f}%")
    return retention_90d

def calculate_ltv(arpu, retention_90d):
    """LTV — простой расчёт."""
    avg_purchases = 1 + (retention_90d / 100) * 0.5
    ltv = arpu * avg_purchases
    print(f"\n=== LTV ===")
    print(f"Среднее покупок/пользователь (6 мес): {avg_purchases:.2f}")
    print(f"LTV: {ltv:.0f}")
    return ltv

def generate_report(transactions, events):
    """Генерация текстового отчёта."""
    arpu = calculate_arpu(transactions)
    funnel = calculate_funnel(events)
    retention = calculate_retention(transactions)
    ltv = calculate_ltv(arpu, retention)

    report = f"""
# [Название продукта] — Business Metrics Report
Date: {pd.Timestamp.now().strftime('%Y-%m-%d')}

## Key Metrics
- Total Orders: {len(transactions):,}
- Total Revenue: {(transactions['base_price'].sum()):,.0f}
- ARPU: {arpu:.0f}
- LTV: {ltv:.0f}
- 90-day Retention: {retention:.1f}%

## Funnel
{chr(10).join(f'- {k}: {v:,}' for k, v in funnel.items())}
"""

    report_path = OUTPUT_DIR / "business_metrics_report.md"
    report_path.write_text(report, encoding="utf-8")
    print(f"\nОтчёт сохранён: {report_path}")

if __name__ == "__main__":
    transactions = pd.read_csv(DATA_DIR / "transactions.csv", parse_dates=["created_at"])
    events = pd.read_csv(DATA_DIR / "events.csv", parse_dates=["created_at"])
    generate_report(transactions, events)
```

### 4. Скрипт 3: Cohort Analysis

Файл: `data/output/14-python-pipeline/scripts/03_cohort_analysis.py`

```python
import pandas as pd
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt
from pathlib import Path

DATA_DIR = Path("data/input/data")
OUTPUT_DIR = Path("data/output/14-python-pipeline/output/cohorts")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

def build_cohort_table(transactions):
    """Когортная таблица retention по месяцам регистрации."""
    transactions["cohort_month"] = transactions.groupby("user_id")["created_at"].transform("min").dt.to_period("M")
    transactions["purchase_month"] = transactions["created_at"].dt.to_period("M")
    transactions["months_since_first"] = (
        transactions["purchase_month"] - transactions["cohort_month"]
    ).apply(lambda x: x.n)

    cohort_data = (
        transactions
        .groupby(["cohort_month", "months_since_first"])["user_id"]
        .nunique()
        .reset_index()
        .rename(columns={"user_id": "users"})
    )

    cohort_pivot = cohort_data.pivot(index="cohort_month", columns="months_since_first", values="users")
    cohort_sizes = cohort_pivot[0]
    retention = cohort_pivot.divide(cohort_sizes, axis=0) * 100

    return retention

def plot_cohort_heatmap(retention):
    """Heatmap когортного retention."""
    plt.figure(figsize=(14, 8))
    sns.heatmap(
        retention,
        annot=True, fmt=".0f",
        cmap="YlOrRd_r",
        linewidths=0.5,
        cbar_kws={"label": "Retention %"}
    )
    plt.title("Cohort Retention Heatmap (% от первой покупки)")
    plt.xlabel("Месяцы с момента первой покупки")
    plt.ylabel("Когорта (месяц первой покупки)")
    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / "cohort_retention_heatmap.png", dpi=150)
    plt.close()
    print(f"Heatmap сохранён в {OUTPUT_DIR}")

if __name__ == "__main__":
    transactions = pd.read_csv(DATA_DIR / "transactions.csv", parse_dates=["created_at"])
    retention = build_cohort_table(transactions)
    plot_cohort_heatmap(retention)
    print(f"\nRetention по когортам (%):\n{retention.round(1)}")
```

### 5. Скрипт 4: Funnel Analysis

Файл: `data/output/14-python-pipeline/scripts/04_funnel_analysis.py`

Включить:
- Построение AARRR воронки с визуализацией (waterfall chart)
- CR между каждым шагом (шаги определить из `data/input/business/workflows.md`)
- Сравнение по ICP-сегментам (из `data/output/02-target-audience/`)
- Выявление шагов с наибольшими потерями

[Предоставить полный код скрипта в том же стиле, что и выше]

### 6. Скрипт 5: Unit Economics Calculator

Файл: `data/output/14-python-pipeline/scripts/05_unit_economics.py`

Включить:
- Расчёт ARPU, CAC, LTV, LTV/CAC, Payback Period из реальных данных
- Сравнение с плановыми показателями из документа 08
- Визуализация план vs факт
- Alerts: если LTV/CAC < 3x или retention ниже порога из `data/output/09-product-metrics/`

[Предоставить полный код]

### 7. Что собирать с первого дня (если данных нет)

Если данных пока нет — настроить трекинг с первого дня после запуска:

| Метрика | Как собирать | Инструмент | Приоритет |
|---------|-------------|-----------|-----------|
| Воронка событий | Event tracking (шаги из workflows.md) | GA4 / Mixpanel / PostHog | Критично |
| Транзакции | Webhook от платёжной системы → БД | (платёжная система из data/info/) | Критично |
| Retention | Связь user_id с событиями | Analytics | Важно |
| Сегменты | При регистрации: спросить «кто вы?» | Форма / Auth metadata | Важно |
| NPS | Опрос после ключевого действия | Typeform / in-app | Важно |

## Требования к качеству

- Все 5 скриптов — рабочий код (не псевдокод, не заготовки)
- Каждый скрипт запускается без ошибок на синтетических данных
- requirements.txt — полный список зависимостей с версиями
- Инструкция по запуску — в `data/output/14-python-pipeline/14-python-pipeline.md`
- Схемы CSV адаптированы под конкретный продукт (не шаблонные)

## Что НЕ делать

- Не писать псевдокод вместо реального Python
- Не пропускать обработку ошибок (try/except для чтения файлов)
- Не хардкодить пути — использовать `pathlib.Path`
- Не забывать UTF-8 при записи файлов на русском языке
- Не использовать шаблонные поля CSV — адаптировать схему под данный продукт из `data/input/`
