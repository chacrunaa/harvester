import argparse
import json
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path


GROUP_ORDER = ["planning", "discovery", "development", "testing", "review"]
PROVIDERS = ("codex", "claude")


@dataclass(frozen=True)
class Project:
    label: str
    path: Path
    notes: Path
    stages_json: Path


def agentforge_root() -> Path:
    return Path(__file__).resolve().parents[3]


def project_label(root: Path, path: Path) -> str:
    try:
        return str(path.relative_to(root / "projects"))
    except ValueError:
        return path.name


def discover_projects(root: Path) -> list[Project]:
    projects_root = root / "projects"
    if not projects_root.exists():
        return []

    found: list[Project] = []
    for candidate in sorted(projects_root.glob("*/*")):
        if not (candidate.is_dir() or candidate.is_symlink()):
            continue
        resolved = candidate.resolve()
        notes = resolved / ".notes"
        stages_json = notes / "tasks" / "backlog" / "stages.json"
        if stages_json.is_file():
            found.append(
                Project(
                    label=project_label(root, candidate),
                    path=resolved,
                    notes=notes,
                    stages_json=stages_json,
                )
            )
    return found


def load_stages(project: Project) -> dict:
    return json.loads(project.stages_json.read_text(encoding="utf-8"))


def groups_from_stages(stages_data: dict) -> dict[str, list[dict]]:
    groups: dict[str, list[dict]] = {}
    for stage in stages_data.get("stages", []):
        groups.setdefault(stage.get("group", "ungrouped"), []).append(stage)
    return groups


def group_alias(group: str) -> str:
    normalized = group.strip().lower()
    for known in GROUP_ORDER:
        if normalized == known or normalized.endswith(f"-{known}"):
            return known
    return normalized


def resolve_group(groups: dict[str, list[dict]], requested: str) -> str | None:
    if requested in groups:
        return requested

    requested_alias = group_alias(requested)
    matches = [group for group in groups if group_alias(group) == requested_alias]
    if len(matches) == 1:
        return matches[0]
    return None


def sort_groups(groups: dict[str, list[dict]]) -> list[str]:
    known = [group for group in GROUP_ORDER if group in groups]
    extra = sorted(group for group in groups if group not in GROUP_ORDER)
    return known + extra


def choose(title: str, options: list[str]) -> str:
    if not options:
        raise SystemExit(f"no options for {title}")

    print(title)
    for idx, option in enumerate(options, start=1):
        print(f"  {idx}. {option}")

    while True:
        raw = input("> ").strip()
        if raw.isdigit():
            index = int(raw)
            if 1 <= index <= len(options):
                return options[index - 1]
        if raw in options:
            return raw
        print(f"choose 1-{len(options)} or exact value")


def agent_docs_for_group(group: str) -> list[str]:
    group_kind = group_alias(group)
    docs = [
        "ai/skills/notes-runtime/SKILL.md",
        "ai/agents/common/notes-stage-worker.md",
        "ai/workflows/software-delivery/workflow.md",
    ]
    if group_kind == "development":
        docs.extend(
            [
                "ai/agents/development/backend-developer.md",
                "ai/agents/development/frontend-developer.md",
            ]
        )
    if group_kind == "testing":
        docs.append("ai/agents/development/tester.md")
    if group_kind == "review":
        docs.append("ai/agents/development/reviewer.md")
    return docs


def project_kind(project: Project) -> str:
    parts = project.label.split("/")
    return parts[0] if len(parts) >= 2 else "work"


PROJECT_KIND_CONTEXT = {
    "work": "Это **рабочий проект** (work). Фокус на командном процессе, бизнес-требованиях, deliverable-ах и качестве.",
    "personal": "Это **личный проект** (personal). Фокус на личных целях и экспериментах автора.",
}


def build_prompt(root: Path, project: Project, group: str, stages: list[dict]) -> str:
    docs = "\n".join(f"- {doc}" for doc in agent_docs_for_group(group))
    stage_ids = ", ".join(stage.get("id", "") for stage in stages)
    kind_context = PROJECT_KIND_CONTEXT.get(project_kind(project), "")

    return f"""Ты group-holder агент `{group}` для проекта:

{project.path}

{kind_context}

Работай только с этим проектом и его `.notes`.

AgentForge root:
{root}

Обязательно сначала прочитай reusable инструкции:
{docs}

Затем прочитай локальные файлы проекта:
- {project.notes}/tasks/backlog/protocol.md
- {project.notes}/tasks/backlog/stages.json
- README/instructions/experience группы (`{group}`)

Стадии этой группы (только id, для маршрутизации): {stage_ids}.

Инструкции стадий не инлайнятся в этот промпт. Когда возьмёшь задачу, открой
README.md и instructions.md только той стадии, чей id совпадает с
`runtime.current_stage` задачи; соседние стадии группы заранее не читай. Путь
стадии бери из `stages.json -> stages[].directory`.

Если пользователь присылает только TASK_ID, это призыв взять задачу в работу,
но только если её `runtime.current_stage` входит в: {stage_ids}.

Очереди стадий смотри в реальном времени (не из этого промпта):
{root}/app/src/main queues --group {group}

Для изменений состояния используй:
{root}/app/src/main

Не проси пользователя объяснять структуру `.notes`: найди её через
`stages.json -> stages[].directory`, queue.json, README.md и instructions.md.

Перед началом покажи:
1. выбранный проект;
2. выбранную группу;
3. список стадий, которые ты обслуживаешь;
4. какие задачи сейчас лежат в очередях стадий (через `queues --group {group}`).
"""


def run_provider(provider: str, prompt: str, project_path: Path) -> int:
    executable = shutil.which(provider)
    if executable is None:
        print(f"{provider} not found in PATH; prompt printed below.\n")
        print(prompt)
        return 127
    return subprocess.run([executable], input=prompt, text=True, cwd=project_path).returncode


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Start AgentForge project agent chats")
    parser.add_argument("--project", help="Project label, e.g. work/my-service")
    parser.add_argument("--group", help="Agent group, e.g. development")
    parser.add_argument("--provider", choices=PROVIDERS, help="Target chat CLI")
    parser.add_argument("--run", action="store_true", help="Run provider command instead of printing prompt")
    parser.add_argument("--list", action="store_true", help="List projects and groups")
    return parser


def main() -> None:
    args = build_parser().parse_args()
    root = agentforge_root()
    projects = discover_projects(root)

    if args.list:
        if not projects:
            print("no projects with .notes/tasks/backlog/stages.json found")
            return
        for project in projects:
            groups = sort_groups(groups_from_stages(load_stages(project)))
            print(f"{project.label}: {', '.join(groups)}")
        return

    if not projects:
        raise SystemExit("no projects with .notes/tasks/backlog/stages.json found")

    project_by_label = {project.label: project for project in projects}

    if args.project:
        project = project_by_label.get(args.project)
        if project is None:
            raise SystemExit(f"unknown project: {args.project}")
    else:
        project = project_by_label[choose("Which project?", [project.label for project in projects])]

    stages_data = load_stages(project)
    groups = groups_from_stages(stages_data)
    group_options = sort_groups(groups)

    if args.group:
        resolved_group = resolve_group(groups, args.group)
        if resolved_group is None:
            raise SystemExit(f"project {project.label} has no group: {args.group}")
        group = resolved_group
    else:
        group = choose("Which agent group?", group_options)

    provider = args.provider or choose("Which provider?", list(PROVIDERS))
    prompt = build_prompt(root, project, group, groups[group])

    if args.run:
        raise SystemExit(run_provider(provider, prompt, project.path))

    print("\n--- prompt ---\n")
    print(prompt)
    print("--- command ---")
    print(f"cd {project.path}")
    print(f"{provider}")


if __name__ == "__main__":
    main()
