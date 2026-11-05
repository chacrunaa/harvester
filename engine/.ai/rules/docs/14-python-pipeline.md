---
id: 14-python-pipeline
title: 14. Python-пайплайн для анализа данных
sidebar_position: 15
---

# Инструкция 14 — Python-пайплайн для анализа данных

## Роль AI-агента

> Ты опытный data analyst и Python-разработчик. Твоя задача — написать готовый Python-скрипт (или набор скриптов), который пользователь запустит локально и получит конкретные числа, графики и выводы по своим данным. Код должен быть понятным, запускаемым с минимальной настройкой и документированным.

## Когда использовать эту инструкцию

Эта инструкция нужна когда:
- Есть CSV/Excel файл с реальными данными продукта (транзакции, события, пользователи)
- Нужно самостоятельно посчитать и **проверить** цифры из других бизнес-документов
- Хочется визуализировать данные, найти аномалии или подтвердить гипотезы
- Нужен автоматизированный скрипт вместо ручного анализа в Excel

---

## Входные данные

Передай агенту:
- Описание задачи (что хочешь посчитать / проверить)
- Структуру данных: названия колонок, типы, пример строк
- Целевые метрики (CAC, LTV, Retention, Churn, ARPU и т.д.)
- Файлы данных (укажи путь или прикрепи образец)

---

## Шаблон 1 — Разведочный анализ данных (EDA)

**Задача:** быстро понять, что за данные, есть ли аномалии, как они распределены.

```python
# ============================================================
# EDA PIPELINE — Exploratory Data Analysis
# Использует: pandas, numpy, matplotlib
# Запуск: python eda_pipeline.py
# ============================================================

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import warnings
warnings.filterwarnings('ignore')

# --- 1. ЗАГРУЗКА ДАННЫХ ---
# Укажи путь к своему файлу
df = pd.read_csv('data/your_data.csv', sep=',', encoding='utf-8')
# Для Excel: df = pd.read_excel('data/your_data.xlsx')

print("=" * 50)
print("1. ОБЗОР ДАННЫХ")
print("=" * 50)
print(f"Размер: {df.shape[0]} строк, {df.shape[1]} колонок")
print(f"\nКолонки: {list(df.columns)}")
print(f"\nПервые 5 строк:\n{df.head()}")
print(f"\nТипы данных:\n{df.dtypes}")

# --- 2. КАЧЕСТВО ДАННЫХ ---
print("\n" + "=" * 50)
print("2. КАЧЕСТВО ДАННЫХ")
print("=" * 50)

# Пропуски
missing = df.isnull().mean().sort_values(ascending=False)
missing_pct = (missing * 100).round(2)
print(f"\nПроцент пропусков по колонкам:\n{missing_pct[missing_pct > 0]}")

# Дубликаты
dupes = df.duplicated().sum()
print(f"\nДубликатов: {dupes} ({dupes/len(df)*100:.1f}%)")

# Удаляем дубликаты
df = df.drop_duplicates()
print(f"После удаления дубликатов: {len(df)} строк")

# --- 3. ОПИСАТЕЛЬНАЯ СТАТИСТИКА ---
print("\n" + "=" * 50)
print("3. ОПИСАТЕЛЬНАЯ СТАТИСТИКА")
print("=" * 50)
print(df.describe().round(2))

# --- 4. РАСПРЕДЕЛЕНИЕ ЧИСЛОВЫХ ПЕРЕМЕННЫХ ---
numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()

fig, axes = plt.subplots(
    nrows=(len(numeric_cols) + 1) // 2,
    ncols=2,
    figsize=(14, 4 * ((len(numeric_cols) + 1) // 2))
)
axes = axes.flatten()

for i, col in enumerate(numeric_cols):
    axes[i].hist(df[col].dropna(), bins=30, color='steelblue', edgecolor='white', linewidth=0.5)
    axes[i].set_title(f'Распределение: {col}')
    axes[i].set_xlabel(col)
    axes[i].set_ylabel('Частота')

plt.tight_layout()
plt.savefig('output/eda_distributions.png', dpi=150)
plt.close()
print("\nГрафики сохранены: output/eda_distributions.png")

# --- 5. МАТРИЦА КОРРЕЛЯЦИИ ---
if len(numeric_cols) > 1:
    corr_matrix = df[numeric_cols].corr()
    
    fig, ax = plt.subplots(figsize=(10, 8))
    im = ax.imshow(corr_matrix, cmap='coolwarm', vmin=-1, vmax=1)
    plt.colorbar(im)
    ax.set_xticks(range(len(numeric_cols)))
    ax.set_yticks(range(len(numeric_cols)))
    ax.set_xticklabels(numeric_cols, rotation=45, ha='right')
    ax.set_yticklabels(numeric_cols)
    
    # Значения в ячейках
    for i in range(len(numeric_cols)):
        for j in range(len(numeric_cols)):
            ax.text(j, i, f'{corr_matrix.iloc[i, j]:.2f}',
                   ha='center', va='center', fontsize=8)
    
    plt.title('Матрица корреляции')
    plt.tight_layout()
    plt.savefig('output/correlation_matrix.png', dpi=150)
    plt.close()
    
    # Сильные корреляции (|r| > 0.7)
    print("\nСильные корреляции (|r| > 0.7):")
    for i in range(len(corr_matrix.columns)):
        for j in range(i+1, len(corr_matrix.columns)):
            r = corr_matrix.iloc[i, j]
            if abs(r) > 0.7:
                print(f"  {corr_matrix.columns[i]} ↔ {corr_matrix.columns[j]}: r={r:.3f}")

print("\n✅ EDA завершён. Результаты в папке output/")
```

---

## Шаблон 2 — Расчёт бизнес-метрик продукта

**Задача:** рассчитать CAC, LTV, ARPU, Churn, Retention из данных транзакций.

**Структура входных данных (пример):**
```
user_id | registration_date | payment_date | amount | channel
```

```python
# ============================================================
# BUSINESS METRICS PIPELINE
# Вычисляет: ARPU, CAC, LTV, Churn Rate, Retention
# Запуск: python metrics_pipeline.py
# ============================================================

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime, timedelta

# --- ЗАГРУЗКА ---
# transactions: user_id, date, amount, channel
transactions = pd.read_csv('data/transactions.csv', parse_dates=['date'])

# users: user_id, registration_date, acquisition_channel
users = pd.read_csv('data/users.csv', parse_dates=['registration_date'])

# marketing_spend: channel, date, spend
marketing = pd.read_csv('data/marketing_spend.csv', parse_dates=['date'])

print("=" * 50)
print("БИЗНЕС-МЕТРИКИ ПРОДУКТА")
print("=" * 50)

# -------------------------------------------------------
# 1. ARPU — Average Revenue Per User
# -------------------------------------------------------
# ARPU = Суммарная выручка / Количество активных пользователей
total_revenue = transactions['amount'].sum()
active_users = transactions['user_id'].nunique()
arpu = total_revenue / active_users

print(f"\n1. ARPU = {total_revenue:,.0f} руб / {active_users} пользователей = {arpu:,.2f} руб")

# ARPU по месяцам
transactions['month'] = transactions['date'].dt.to_period('M')
monthly_arpu = transactions.groupby('month').agg(
    revenue=('amount', 'sum'),
    users=('user_id', 'nunique')
).assign(arpu=lambda x: x['revenue'] / x['users'])
print(f"\nARPU по месяцам:\n{monthly_arpu.round(2)}")

# -------------------------------------------------------
# 2. CAC — Customer Acquisition Cost
# -------------------------------------------------------
# CAC = Маркетинговые расходы / Количество новых клиентов
monthly_spend = marketing.groupby(marketing['date'].dt.to_period('M'))['spend'].sum()
users['reg_month'] = users['registration_date'].dt.to_period('M')
monthly_new_users = users.groupby('reg_month').size().rename('new_users')

cac_df = pd.DataFrame({'spend': monthly_spend, 'new_users': monthly_new_users}).dropna()
cac_df['cac'] = cac_df['spend'] / cac_df['new_users']

print(f"\n2. CAC по месяцам:\n{cac_df.round(2)}")
print(f"\nСредний CAC: {cac_df['cac'].mean():,.2f} руб")

# -------------------------------------------------------
# 3. RETENTION & CHURN RATE
# -------------------------------------------------------
# Retention Rate = Пользователи, вернувшиеся в следующем месяце / Пользователи предыдущего месяца
# Churn Rate = 1 - Retention Rate

def calculate_retention(transactions_df):
    """Когортный анализ retention по месяцам регистрации"""
    # Добавляем месяц первой активности как когорту
    first_activity = transactions_df.groupby('user_id')['date'].min().dt.to_period('M')
    transactions_df = transactions_df.copy()
    transactions_df['cohort'] = transactions_df['user_id'].map(first_activity)
    transactions_df['activity_month'] = transactions_df['date'].dt.to_period('M')
    
    # Считаем активных пользователей по когортам и месяцам
    cohort_data = transactions_df.groupby(['cohort', 'activity_month'])['user_id'].nunique().reset_index()
    cohort_data.columns = ['cohort', 'activity_month', 'users']
    
    # Получаем базовый размер когорты
    cohort_sizes = cohort_data.groupby('cohort')['users'].first()
    
    # Нормализуем
    cohort_data['cohort_size'] = cohort_data['cohort'].map(cohort_sizes)
    cohort_data['retention'] = cohort_data['users'] / cohort_data['cohort_size']
    
    return cohort_data

cohort_data = calculate_retention(transactions)
print(f"\n3. RETENTION (когортный анализ):\n{cohort_data.head(20)}")

# Средний Retention M1 (через 1 месяц после регистрации)
# Churn Rate = 1 - Retention
avg_retention = cohort_data.groupby('activity_month')['retention'].mean()
print(f"\nСредний Retention Rate: {avg_retention.mean()*100:.1f}%")
print(f"Средний Churn Rate: {(1-avg_retention.mean())*100:.1f}%")

# -------------------------------------------------------
# 4. LTV — Lifetime Value
# -------------------------------------------------------
# LTV = ARPU × Gross Margin × (1 / Churn Rate)
# Simplified: LTV = ARPU monthly × Average lifetime months

avg_churn_rate = 1 - avg_retention.mean()
avg_lifetime_months = 1 / avg_churn_rate if avg_churn_rate > 0 else 0
gross_margin = 0.70  # Укажи реальную маржу вашего продукта

ltv = arpu * gross_margin * avg_lifetime_months

print(f"\n4. LTV расчёт:")
print(f"   ARPU monthly      = {arpu:,.2f} руб")
print(f"   Gross Margin      = {gross_margin*100:.0f}%")
print(f"   Avg Churn Rate    = {avg_churn_rate*100:.1f}%")
print(f"   Avg Lifetime      = {avg_lifetime_months:.1f} мес")
print(f"   LTV               = {ltv:,.2f} руб")

# -------------------------------------------------------
# 5. LTV / CAC RATIO
# -------------------------------------------------------
avg_cac = cac_df['cac'].mean()
ltv_cac_ratio = ltv / avg_cac if avg_cac > 0 else 0

print(f"\n5. LTV/CAC Ratio:")
print(f"   LTV = {ltv:,.2f} руб")
print(f"   CAC = {avg_cac:,.2f} руб")
print(f"   LTV/CAC = {ltv_cac_ratio:.2f}x")

if ltv_cac_ratio < 1:
    print("   ⚠️  КРИТИЧНО: Каждый клиент приносит убыток")
elif ltv_cac_ratio < 3:
    print("   ⚠️  РИСК: Соотношение ниже нормы (норма ≥ 3x)")
else:
    print("   ✅  НОРМА: Бизнес-модель экономически жизнеспособна")

# -------------------------------------------------------
# 6. ВИЗУАЛИЗАЦИЯ
# -------------------------------------------------------
fig, axes = plt.subplots(2, 2, figsize=(14, 10))

# ARPU динамика
monthly_arpu['arpu'].plot(ax=axes[0][0], marker='o', color='steelblue')
axes[0][0].set_title('ARPU по месяцам (руб)')
axes[0][0].grid(True, alpha=0.3)

# CAC динамика
cac_df['cac'].plot(ax=axes[0][1], marker='s', color='tomato')
axes[0][1].set_title('CAC по месяцам (руб)')
axes[0][1].grid(True, alpha=0.3)

# Retention heatmap (упрощённый)
retention_pivot = cohort_data.pivot_table(
    values='retention', index='cohort', columns='activity_month', fill_value=0
)
im = axes[1][0].imshow(retention_pivot.values, cmap='YlGn', vmin=0, vmax=1)
axes[1][0].set_title('Retention Map (когорты)')
plt.colorbar(im, ax=axes[1][0])

# LTV/CAC bar
labels = ['LTV', 'CAC', 'LTV/CAC × 10']
values = [ltv, avg_cac, ltv_cac_ratio * 10]
colors = ['green', 'red', 'steelblue']
axes[1][1].bar(labels, values, color=colors, alpha=0.7)
axes[1][1].set_title('LTV vs CAC (LTV/CAC × 10 для масштаба)')
axes[1][1].axhline(y=avg_cac * 3, color='orange', linestyle='--', label='LTV/CAC=3x benchmark')
axes[1][1].legend()

plt.tight_layout()
plt.savefig('output/business_metrics.png', dpi=150)
plt.close()

print("\n✅ Расчёт завершён. Графики: output/business_metrics.png")
```

---

## Шаблон 3 — Когортный анализ (Retention/Churn)

**Задача:** построить когортную таблицу и heatmap retention.

```python
# ============================================================
# COHORT ANALYSIS PIPELINE
# Входные данные: user_id, date, amount (транзакции)
# ============================================================

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker

# Загрузка
df = pd.read_csv('data/transactions.csv', parse_dates=['date'])

# --- Создание когорт ---
df['cohort_month'] = df.groupby('user_id')['date'].transform('min').dt.to_period('M')
df['activity_month'] = df['date'].dt.to_period('M')

# Период с момента первой транзакции (0, 1, 2, ... месяцев)
df['period_number'] = (
    df['activity_month'].astype(int) - df['cohort_month'].astype(int)
)

# --- Когортная таблица (количество пользователей) ---
cohort_table = df.groupby(['cohort_month', 'period_number'])['user_id'].nunique().reset_index()
cohort_pivot = cohort_table.pivot_table(
    index='cohort_month', columns='period_number', values='user_id'
)

# Размеры когорт (период 0)
cohort_sizes = cohort_pivot[0]

# --- Retention rate table ---
retention_table = cohort_pivot.divide(cohort_sizes, axis=0)

print("КОГОРТНАЯ ТАБЛИЦА (Retention Rate):")
print(retention_table.round(3))

# Средний Retention по периодам
avg_retention_by_period = retention_table.mean()
print(f"\nСредний Retention по периодам:")
for period, rate in avg_retention_by_period.items():
    print(f"  M{period}: {rate*100:.1f}%")

# --- Heatmap ---
fig, ax = plt.subplots(figsize=(16, 8))

# Заменяем NaN на 0 для отображения
display_table = retention_table.fillna(0)

im = ax.imshow(display_table.values, cmap='YlGn', vmin=0, vmax=1, aspect='auto')
plt.colorbar(im, ax=ax, label='Retention Rate')

# Подписи
ax.set_xticks(range(len(display_table.columns)))
ax.set_xticklabels([f'M{i}' for i in display_table.columns])
ax.set_yticks(range(len(display_table.index)))
ax.set_yticklabels([str(c) for c in display_table.index])

# Значения в ячейках
for i in range(len(display_table.index)):
    for j in range(len(display_table.columns)):
        val = display_table.iloc[i, j]
        if val > 0:
            color = 'white' if val > 0.5 else 'black'
            ax.text(j, i, f'{val*100:.0f}%', ha='center', va='center',
                   fontsize=8, color=color)

ax.set_title('Когортный анализ: Retention Rate по месяцам', fontsize=14)
ax.set_xlabel('Период после регистрации')
ax.set_ylabel('Когорта (месяц регистрации)')

plt.tight_layout()
plt.savefig('output/cohort_retention.png', dpi=150)
plt.close()

print("\n✅ Когортный анализ завершён. Heatmap: output/cohort_retention.png")
```

---

## Шаблон 4 — Анализ воронки конверсии (AARRR)

**Задача:** посчитать конверсию на каждом шаге воронки.

```python
# ============================================================
# FUNNEL ANALYSIS — AARRR метрики
# Входные данные: events (user_id, event_name, date)
# ============================================================

import pandas as pd
import matplotlib.pyplot as plt

events = pd.read_csv('data/events.csv', parse_dates=['date'])

# --- Определяем воронку ---
# Настрой этапы под свой продукт
FUNNEL_STEPS = [
    'registration',      # Acquisition
    'onboarding_done',   # Activation
    'first_payment',     # Revenue
    'second_payment',    # Retention
    'referral_sent',     # Referral
]

# Считаем уникальных пользователей на каждом шаге
funnel_data = {}
for step in FUNNEL_STEPS:
    users_at_step = events[events['event_name'] == step]['user_id'].nunique()
    funnel_data[step] = users_at_step

funnel_df = pd.DataFrame.from_dict(funnel_data, orient='index', columns=['users'])
funnel_df['conversion_from_prev'] = funnel_df['users'].pct_change() * 100
funnel_df['conversion_from_top'] = funnel_df['users'] / funnel_df['users'].iloc[0] * 100

print("ВОРОНКА КОНВЕРСИИ:")
print(funnel_df.round(1))

# --- Визуализация ---
fig, axes = plt.subplots(1, 2, figsize=(14, 6))

# Воронка (горизонтальный бар)
colors = ['#2196F3', '#4CAF50', '#FF9800', '#9C27B0', '#F44336']
axes[0].barh(
    range(len(FUNNEL_STEPS)),
    funnel_df['users'].values,
    color=colors[:len(FUNNEL_STEPS)],
    alpha=0.8
)
axes[0].set_yticks(range(len(FUNNEL_STEPS)))
axes[0].set_yticklabels(FUNNEL_STEPS)
axes[0].set_xlabel('Количество пользователей')
axes[0].set_title('AARRR Воронка')

# Добавляем конверсию на бары
for i, (users, conv) in enumerate(zip(funnel_df['users'], funnel_df['conversion_from_top'])):
    axes[0].text(users + 10, i, f'{users:,} ({conv:.1f}%)', va='center')

# Конверсия по шагам
conv_values = funnel_df['conversion_from_prev'].dropna()
axes[1].bar(
    range(len(conv_values)),
    conv_values.values,
    color=['green' if v > -30 else 'red' for v in conv_values],
    alpha=0.8
)
axes[1].set_xticks(range(len(conv_values)))
axes[1].set_xticklabels(
    [f'{FUNNEL_STEPS[i]}→{FUNNEL_STEPS[i+1]}' for i in range(len(conv_values))],
    rotation=30, ha='right'
)
axes[1].set_ylabel('Изменение конверсии (%)')
axes[1].set_title('Конверсия между шагами воронки')
axes[1].axhline(0, color='black', linewidth=0.5)

plt.tight_layout()
plt.savefig('output/funnel_analysis.png', dpi=150)
plt.close()

print("\n✅ Анализ воронки завершён. График: output/funnel_analysis.png")
```

---

## Шаблон 5 — Расчёт юнит-экономики из данных

**Задача:** автоматически рассчитать и вывести финансовую сводку.

```python
# ============================================================
# UNIT ECONOMICS CALCULATOR
# Все ключевые метрики из одного скрипта
# ============================================================

import pandas as pd
import numpy as np

# Загрузи свои данные или задай параметры вручную
# Вариант А: из файла
transactions = pd.read_csv('data/transactions.csv', parse_dates=['date'])
marketing_spend = pd.read_csv('data/marketing_spend.csv')

# Вариант Б: вручную (если данных пока нет)
MANUAL_PARAMS = {
    'monthly_new_users': 500,
    'avg_revenue_per_user_month': 800,   # руб
    'gross_margin_pct': 0.70,            # 70%
    'monthly_churn_rate': 0.12,          # 12%
    'marketing_spend_monthly': 150_000,  # руб
    'avg_order_value': 800,              # руб
    'orders_per_user_per_month': 1.0,
}

def calculate_unit_economics(params):
    """Рассчитывает все метрики юнит-экономики"""
    p = params
    
    # Базовые метрики
    arpu = p['avg_revenue_per_user_month']
    churn = p['monthly_churn_rate']
    retention = 1 - churn
    lifetime_months = 1 / churn
    gross_margin = p['gross_margin_pct']
    
    # CAC
    cac = p['marketing_spend_monthly'] / p['monthly_new_users']
    
    # LTV (два метода)
    # Метод 1: LTV = ARPU × Margin × Lifetime
    ltv_method1 = arpu * gross_margin * lifetime_months
    
    # Метод 2: LTV через Retention (более точный)
    # LTV = ARPU × Margin / (1 - Retention)  =  ARPU × Margin / Churn
    ltv_method2 = (arpu * gross_margin) / churn
    
    ltv = ltv_method1  # используем метод 1
    
    # Ключевые соотношения
    ltv_cac = ltv / cac
    payback_months = cac / (arpu * gross_margin)
    
    # Точка безубыточности
    # Предполагаем фиксированные расходы = маркетинг × 2 (упрощённо)
    fixed_costs = p['marketing_spend_monthly'] * 2
    variable_cost_per_user = arpu * (1 - gross_margin)
    contribution_per_user = arpu - variable_cost_per_user
    breakeven_users = fixed_costs / contribution_per_user
    
    results = {
        '--- ДОХОДЫ ---': '',
        'ARPU (месяц)': f"{arpu:,.0f} руб",
        'ARPPU (с учётом margin)': f"{arpu * gross_margin:,.0f} руб",
        
        '--- ПРИВЛЕЧЕНИЕ ---': '',
        'CAC': f"{cac:,.0f} руб",
        
        '--- УДЕРЖАНИЕ ---': '',
        'Monthly Retention Rate': f"{retention*100:.1f}%",
        'Monthly Churn Rate': f"{churn*100:.1f}%",
        'Avg Customer Lifetime': f"{lifetime_months:.1f} мес",
        
        '--- LTV ---': '',
        'LTV (метод 1: ARPU×Margin×Lifetime)': f"{ltv_method1:,.0f} руб",
        'LTV (метод 2: ARPU×Margin/Churn)': f"{ltv_method2:,.0f} руб",
        
        '--- КЛЮЧЕВЫЕ СООТНОШЕНИЯ ---': '',
        'LTV/CAC': f"{ltv_cac:.2f}x",
        'Payback Period': f"{payback_months:.1f} мес",
        
        '--- ТОЧКА БЕЗУБЫТОЧНОСТИ ---': '',
        'Break-even пользователей': f"{breakeven_users:.0f}",
        
        '--- ОЦЕНКА ---': '',
        'Статус LTV/CAC': (
            '✅ ОТЛИЧНО (>3x)' if ltv_cac > 3 else
            '⚠️  РИСК (1-3x)' if ltv_cac > 1 else
            '🚨 УБЫТОК (<1x)'
        ),
        'Статус Payback': (
            '✅ НОРМА (<12 мес)' if payback_months < 12 else
            '⚠️  ДОЛГО (12-24 мес)' if payback_months < 24 else
            '🚨 КРИТИЧНО (>24 мес)'
        ),
    }
    return results

# Запуск
print("=" * 55)
print("     ЮНИТ-ЭКОНОМИКА — РАСЧЁТНЫЙ ОТЧЁТ")
print("=" * 55)

results = calculate_unit_economics(MANUAL_PARAMS)
for key, value in results.items():
    if key.startswith('---'):
        print(f"\n{key}")
    else:
        print(f"  {key:<40} {value}")

print("\n" + "=" * 55)
print("✅ Расчёт завершён")
```

---

## Структура проекта для запуска пайплайнов

```
your_project/
├── data/
│   ├── transactions.csv
│   ├── users.csv
│   ├── marketing_spend.csv
│   └── events.csv
├── output/
│   └── (здесь появятся графики и отчёты)
├── requirements.txt
├── eda_pipeline.py
├── metrics_pipeline.py
├── cohort_pipeline.py
├── funnel_pipeline.py
└── unit_economics.py
```

**requirements.txt:**
```
pandas>=2.0.0
numpy>=1.24.0
matplotlib>=3.7.0
plotly>=5.15.0
openpyxl>=3.1.0
```

**Установка зависимостей:**
```bash
pip install -r requirements.txt
```

---

## Структура входных данных (минимально необходимая)

### transactions.csv
```
user_id,date,amount,channel
1001,2024-01-05,800,organic
1002,2024-01-06,1200,paid_search
1001,2024-02-10,800,organic
```

### users.csv
```
user_id,registration_date,acquisition_channel
1001,2024-01-03,organic
1002,2024-01-05,paid_search
```

### marketing_spend.csv
```
channel,date,spend
paid_search,2024-01-01,50000
social_ads,2024-01-01,30000
```

### events.csv
```
user_id,event_name,date
1001,registration,2024-01-03
1001,onboarding_done,2024-01-04
1001,first_payment,2024-01-05
```

---

## Как агент должен кастомизировать шаблоны

При генерации кода агент обязан:

1. **Адаптировать названия колонок** под реальную структуру входных данных
2. **Указать конкретные пороговые значения** (Gross Margin, целевой Churn) из бизнес-модели
3. **Настроить этапы воронки** под реальный продукт (не generic registration/payment)
4. **Добавить комментарии** — каждый блок кода объяснён 1–2 строками
5. **Обеспечить запускаемость** — код должен работать `python script.py` без дополнительных настроек
6. **Сохранять результаты** — все числа выводятся в консоль + графики сохраняются в `output/`

---

## Критерии качества

- [ ] Скрипт запускается командой `python script.py` без ошибок
- [ ] Все зависимости перечислены в `requirements.txt`
- [ ] Входные данные описаны с примерами (первые 3 строки CSV)
- [ ] Все расчёты совпадают с формулами из инструкции 08 (юнит-экономика)
- [ ] Графики сохраняются в `output/` автоматически
- [ ] Комментарии на русском, код на английском
- [ ] Результаты выводятся в читаемом формате с единицами измерения
