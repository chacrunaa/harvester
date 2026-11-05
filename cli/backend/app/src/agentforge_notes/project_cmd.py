from pathlib import Path

HARV_CONFIG = Path.home() / ".harv" / "active"

GROUP_DIRS = {
    "planning": "plan",
    "dev":      "dev",
    "testing":  "testing",
    "review":   "review",
}


def _backend_root() -> Path:
    return Path(__file__).resolve().parents[3]


def _active_project() -> str:
    if not HARV_CONFIG.exists():
        print("error: нет активного проекта. Выполните: harv use <project>", flush=True)
        raise SystemExit(1)
    return HARV_CONFIG.read_text(encoding="utf-8").strip()


def cmd_use(args):
    label = args.project.strip().lstrip("/")
    backend = _backend_root()
    project_path = backend / "projects" / label
    if not project_path.exists():
        print(f"error: проект не найден: {project_path}", flush=True)
        raise SystemExit(1)
    resolved = project_path.resolve()
    notes = resolved / ".notes"
    if not (notes / "tasks" / "backlog" / "stages.json").is_file():
        print(f"error: .notes/ не инициализирован. Выполните: harv init {resolved}", flush=True)
        raise SystemExit(1)
    HARV_CONFIG.parent.mkdir(parents=True, exist_ok=True)
    HARV_CONFIG.write_text(label + "\n", encoding="utf-8")
    print(f"активный проект: {label} ({resolved})")


def cmd_group(args):
    group_dir = GROUP_DIRS[args.command]
    label = _active_project()
    backend = _backend_root()
    project_path = (backend / "projects" / label).resolve()
    instructions = project_path / ".notes" / "tasks" / "backlog" / group_dir / "instructions.md"
    if not instructions.is_file():
        print(f"error: инструкции не найдены: {instructions}", flush=True)
        raise SystemExit(1)
    print(instructions.read_text(encoding="utf-8"))
