PYTHON ?= python3
HARV   := app/src/main
FORGE  := app/src/forge
ROOT   := $(CURDIR)

.PHONY: help install check test projects chat

help:
	@printf '%s\n' \
		'Harvester v2 — CLI harv' \
		'' \
		'Make:' \
		'  make install               Создать обёртку dist/harv' \
		'  make check                 Компиляция Python + smoke-test CLI' \
		'  make test                  65 тестов (unittest)' \
		'  make projects              Список подключённых проектов' \
		'  make chat                  Интерактивный выбор проекта и группы' \
		'' \
		'Подключение проекта:' \
		'  harv init /path --work     Инициализировать рабочий проект' \
		'  harv init /path --personal Инициализировать личный проект' \
		'  harv use personal/my-app   Переключить активный проект' \
		'' \
		'Задачи:' \
		'  harv create "описание"     Создать задачу' \
		'  harv status HARV-001       Состояние задачи' \
		'  harv advance HARV-001      Передать задачу на следующую стадию' \
		'  harv validate              Проверить целостность .notes/' \
		'' \
		'Полный список — harv --help (24 команды).'

install:
	@mkdir -p dist
	@printf '#!/usr/bin/env bash\nexec "$(ROOT)/$(HARV)" "$$@"\n' > dist/harv
	@chmod +x dist/harv
	@echo "dist/harv готов. Для глобального доступа:"
	@echo "  ln -sf $(ROOT)/dist/harv ~/.local/bin/harv"

check:
	$(PYTHON) -m compileall -q app/src/agentforge_launcher app/src/agentforge_notes
	$(FORGE) --list
	$(ROOT)/$(HARV) --help

# Пакеты лежат в app/src, который не на sys.path по умолчанию:
# без PYTHONPATH падает импорт в test_cli.py.
test:
	PYTHONPATH=app/src $(PYTHON) -m unittest discover -s app/tests -t app/tests

projects:
	$(FORGE) --list

chat:
	$(FORGE)
