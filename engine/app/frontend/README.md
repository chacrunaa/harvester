# Harvester Frontend

React 18 + TypeScript + Vite. Web и Tauri-desktop из одной кодовой базы.

## Установка

```bash
# 1. Зависимости фронта
npm install

# 2. Локальные env-файлы (шаблон в .env.example)
cp .env.example .env.web
cp .env.example .env.desktop
```

## Запуск (web)

```bash
npm run dev          # http://127.0.0.1:5173
npm run build        # prod-бандл в dist/
npm run typecheck
npm run lint
```

## Запуск (desktop, Tauri v2)

Требуется Rust toolchain.

### Установка Rust

```bash
# 1. Поставить rustup (интерактивный установщик, выбери 1 — default install)
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh

# 2. Подгрузить PATH без перезапуска терминала
source "$HOME/.cargo/env"

# 3. Проверить
rustc --version
cargo --version
```

### Запуск desktop-режима

```bash
npm run tauri:dev    # нативное окно с hot reload
npm run tauri:build  # prod-бандл (.app/.dmg/.msi/.AppImage) в src-tauri/target/release/bundle/
```

Первый `tauri:dev` долгий (~2–5 минут): cargo качает и компилирует Rust-зависимости. Последующие запуски — инкрементальные, быстрые.

## Структура

См. `docs/structure/architecture.md` и `docs/rules/architecture.md`.
