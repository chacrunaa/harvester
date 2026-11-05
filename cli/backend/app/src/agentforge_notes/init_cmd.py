import json
import shutil
from pathlib import Path


def _store_template() -> Path:
    return Path(__file__).resolve().parents[3] / "store" / "examples" / "notes"


def _detect(target: Path, names) -> str:
    """Вернуть первый существующий каталог из names, иначе первый кандидат."""
    for n in names:
        if (target / n).is_dir():
            return n
    return names[0]


def _resolve_code_roots(args, target: Path) -> dict:
    return {
        "CODE_BACKEND": args.backend or _detect(target, ["backend", "server", "api"]),
        "CODE_UI": args.ui or _detect(target, ["frontend", "ui", "web", "client"]),
        "CODE_DOCS": args.docs or _detect(target, ["documentations", "docs", "documentation"]),
    }


def _apply_code_roots(notes_dir: Path, roots: dict) -> None:
    """Подставить {{CODE_*}} плейсхолдеры во всех инструкциях/README .notes."""
    for path in list(notes_dir.rglob("instructions.md")) + list(notes_dir.rglob("README.md")):
        text = path.read_text(encoding="utf-8")
        new = text
        for key, value in roots.items():
            new = new.replace("{{" + key + "}}", value)
        if new != text:
            path.write_text(new, encoding="utf-8")
    backlog = notes_dir / "tasks" / "backlog"
    if backlog.is_dir():
        (backlog / "project.json").write_text(
            json.dumps({"code_roots": roots}, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )


def cmd_init(args):
    target = Path(args.path).resolve()
    notes_dir = target / ".notes"
    template = _store_template()
    if not template.is_dir():
        print(f"error: шаблон не найден: {template}", flush=True)
        raise SystemExit(1)
    if notes_dir.exists():
        if not args.force:
            print(f"error: {notes_dir} уже существует. Используйте --force для перезаписи", flush=True)
            raise SystemExit(1)
        shutil.rmtree(notes_dir)
    shutil.copytree(template, notes_dir)

    roots = _resolve_code_roots(args, target)
    _apply_code_roots(notes_dir, roots)
    print(f"code-roots: backend={roots['CODE_BACKEND']} ui={roots['CODE_UI']} docs={roots['CODE_DOCS']}")

    kind = args.kind  # "work" or "personal"
    project_name = target.name
    backend = Path(__file__).resolve().parents[3]
    projects_dir = backend / "projects" / kind
    projects_dir.mkdir(parents=True, exist_ok=True)
    link = projects_dir / project_name
    if not link.exists():
        link.symlink_to(target)
        print(f"инициализирован: {notes_dir}")
        print(f"зарегистрирован: projects/{kind}/{project_name} → {target}")
    else:
        print(f"инициализирован: {notes_dir}")
        print(f"симлинк уже существует: projects/{kind}/{project_name}")

    label = f"{kind}/{project_name}"
    from .project_cmd import HARV_CONFIG
    HARV_CONFIG.parent.mkdir(parents=True, exist_ok=True)
    HARV_CONFIG.write_text(f"{label}\n", encoding="utf-8")
    print(f"активный проект: {label}")
