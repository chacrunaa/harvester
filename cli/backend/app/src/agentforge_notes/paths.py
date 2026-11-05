import json
import sys
from pathlib import Path


def find_notes_root():
    # 1. Search CWD and its parents.
    cwd = Path.cwd().absolute()
    seen = set()
    for base in [cwd, *cwd.parents]:
        if base in seen:
            continue
        seen.add(base)
        candidate = base / ".notes"
        if candidate.is_dir() and (candidate / "tasks" / "backlog" / "stages.json").is_file():
            return candidate

    # 2. Fall back to active project from ~/.harv/active.
    harv_active = Path.home() / ".harv" / "active"
    if harv_active.is_file():
        label = harv_active.read_text(encoding="utf-8").strip()
        backend = Path(__file__).resolve().parents[3]
        project_link = backend / "projects" / label
        if project_link.exists():
            candidate = project_link.resolve() / ".notes"
            if candidate.is_dir() and (candidate / "tasks" / "backlog" / "stages.json").is_file():
                return candidate

    print("error: cannot find .notes from current directory", file=sys.stderr)
    print("hint: выполни 'harv use work/<project>' чтобы задать активный проект", file=sys.stderr)
    raise SystemExit(1)


ROOT = find_notes_root()
BACKLOG = ROOT / "tasks" / "backlog"
HISTORY = ROOT / "history"
TASKS_DIR = HISTORY / "tasks"
RUNS_DIR = HISTORY / "runs"
HANDOFFS_DIR = HISTORY / "handoffs"
TASKS_JSON = BACKLOG / "tasks.json"
STAGES_JSON = BACKLOG / "stages.json"


def task_dir(task_id):
    return TASKS_DIR / task_id


def runs_task_dir(task_id):
    return RUNS_DIR / task_id


def run_dir(task_id, run_id):
    return RUNS_DIR / task_id / run_id


def group_run_dir(task_id, group_run_id):
    return RUNS_DIR / task_id / group_run_id


def handoff_dir(task_id):
    return HANDOFFS_DIR / task_id


def task_json_path(task_id):
    return task_dir(task_id) / "task.json"


def stage_dir(stage):
    data = json.loads(STAGES_JSON.read_text(encoding="utf-8"))
    for item in data.get("stages", []):
        if item.get("id") == stage:
            return BACKLOG / item.get("directory", stage)
    print(f"error: unknown stage: {stage}", file=sys.stderr)
    raise SystemExit(1)


def queue_path(stage):
    return stage_dir(stage) / "queue.json"
