---
name: figma-designer
description: Запускает figma-designer агента для построения и обновления макетов в Figma по шаблону дизайн-системы.
argument-hint: "<описание задачи>"
---

[FIGMA-DESIGNER ACTIVATED]

Запусти агента `figma-designer` для выполнения задачи пользователя.

<Pre_Check>
Если `{{PROMPT}}` пустой или короче 3 слов — остановись и выведи:
```
Опиши задачу после команды. Например:
  /figma-designer добавить карточку отчёта типа result на страницу раздела Разработка
  /figma-designer обновить SubChatPanel — добавить вкладку "Тестирование"
```
</Pre_Check>

<Launch>
Запусти агента:

```
Agent(
  subagent_type="figma-designer",
  prompt="
Задача от пользователя: {{PROMPT}}

Контекст:
- Шаблон дизайн-системы: research/design-system-template.md — читать ПЕРВЫМ делом
- Figma fileKey: UspW8rBkJRNase4iQaMrCa
- Ключевые узлы: каркас 123:1714, отчёты 124:1553, общие элементы 122:1478

Порядок работы:
1. Прочитай research/design-system-template.md
2. Получи контекст затрагиваемого узла через get_design_context
3. Если задача требует элемента, которого нет в шаблоне — СТОП, сообщи пользователю что именно отсутствует
4. Реализуй изменения в Figma
5. Сделай get_screenshot для верификации
6. Если добавлен новый согласованный элемент — обнови research/design-system-template.md

Завершив, выведи отчёт: что сделано, какие nodeId изменены, скриншот, обновлён ли шаблон.
  "
)
```
</Launch>

Original request: {{PROMPT}}
