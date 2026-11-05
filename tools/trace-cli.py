#!/usr/bin/env python3
"""Реальный прогон harv в изолированном окружении + запись трассы для витрины.

Ничего не трогает за пределами временных каталогов: HOME подменяется,
целевой проект создаётся в tmp. Ключи LLM не нужны — harv не ходит в сеть.

Артефакты стадий создаются так, как их создавал бы агент: пустые
заглушки по путям из required_outputs_on_success. Нас интересует
поведение машины состояний, а не содержимое документов.
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
BACKEND = REPO / "cli" / "backend"
HARV = BACKEND / "app" / "src" / "main"
TASK = "HARV-004"


def main():
    tmp = Path(tempfile.mkdtemp(prefix="harv-trace-"))
    home = tmp / "home"
    project = tmp / "demo-project"
    home.mkdir()
    project.mkdir()
    (project / "README.md").write_text("# demo\n")

    env = {**os.environ, "HOME": str(home), "PYTHONPATH": str(BACKEND / "app" / "src")}
    notes = project / ".notes"
    steps = []

    def harv(args, cwd=project):
        return subprocess.run(
            [str(HARV), *args], capture_output=True, text=True, env=env, cwd=str(cwd)
        )

    def snapshot(label, command, result, note=""):
        task_file = notes / "history" / "tasks" / TASK / "task.json"
        runtime = {}
        if task_file.exists():
            data = json.loads(task_file.read_text())
            rt = data.get("runtime", {})
            lease = rt.get("lease") or {}
            runtime = {
                "stage": rt.get("current_stage"),
                "status": rt.get("status"),
                "revision": rt.get("revision"),
                "owner": lease.get("owner"),
                "artifacts": len(data.get("artifacts", []) or []),
                "events": len(data.get("events", []) or []),
            }
        queues = {}
        for q in sorted(notes.glob("tasks/backlog/*/stages/*/queue.json")):
            raw = json.loads(q.read_text())
            ids = raw.get("items", raw) if isinstance(raw, dict) else raw
            if isinstance(ids, list) and ids:
                queues[q.parent.name] = [i if isinstance(i, str) else str(i) for i in ids]
        ok = result.returncode == 0
        out = ((result.stdout or "") + (result.stderr or "")).strip()
        steps.append({
            "label": label,
            "command": command,
            "note": note,
            "ok": ok,
            "exit": result.returncode,
            "output": out[:700],
            "runtime": runtime,
            "queues": queues,
        })
        print(f"  [{result.returncode}] {command}")
        return result

    def complete_stage(stage_id, register=True):
        """Создать и зарегистрировать обязательные артефакты стадии.

        Гейт требует и наличия файла, и записи о нём в task.json —
        поэтому после записи вызываем add-artifact.
        """
        created = make_required_artifacts(stage_id)
        if register:
            for rel in created:
                harv(["add-artifact", TASK, "--type", "report", "--path", rel])
        return created

    def make_required_artifacts(stage_id):
        """Создать файлы, которые стадия обязана оставить после себя."""
        stages = json.loads((notes / "tasks/backlog/stages.json").read_text())["stages"]
        stage = next((s for s in stages if s["id"] == stage_id), None)
        if not stage:
            return []
        created = []
        for tpl in stage.get("required_outputs_on_success", []):
            rel = tpl.replace("<TASK_ID>", TASK)
            path = notes / rel
            # Часть требуемых выходов — служебные файлы (task.json,
            # source.txt), которые уже существуют. Их не трогаем.
            if path.exists():
                continue
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(
                f"# {Path(rel).stem}\n\n"
                f"Артефакт стадии `{stage_id}` задачи {TASK}.\n"
                f"Создан автоматически при записи демонстрационного прогона.\n"
            )
            created.append(rel)
        return created

    print("Прогон harv в", tmp)

    snapshot("init", "harv init <project> --personal",
             harv(["init", str(project), "--personal"], cwd=BACKEND),
             "создаёт .notes/ из store/examples/notes и подключает проект")

    snapshot("create", 'harv create "Добавить экспорт отчётов в CSV"',
             harv(["create", "Добавить экспорт отчётов в CSV"]),
             f"задача {TASK} заходит в стадию intake")

    snapshot("status", f"harv status {TASK}", harv(["status", TASK]),
             "состояние задачи: стадия, статус, ревизия")

    snapshot("take", f"harv take {TASK} --stage intake --owner planning-terminal",
             harv(["take", TASK, "--stage", "intake", "--owner", "planning-terminal"]),
             "агент берёт задачу — ставится lease на 120 минут")

    complete_stage("intake")
    snapshot("advance-analysis", f"harv advance {TASK} --to analysis",
             harv(["advance", TASK, "--to", "analysis", "--owner", "planning-terminal"]),
             "валидирующая передача: переход сверяется с картой стадий")

    snapshot("gate-blocked", f"harv advance {TASK} --to architecture",
             harv(["advance", TASK, "--to", "architecture", "--owner", "planning-terminal"]),
             "ГЕЙТ сработал: стадия analysis обязана оставить 3 артефакта — передача отклонена")

    created = complete_stage("analysis")
    snapshot("artifacts-added", f"harv artifacts {TASK}",
             harv(["artifacts", TASK]),
             f"агент выложил {len(created)} обязательных артефакта и зарегистрировал их через add-artifact")

    snapshot("advance-architecture", f"harv advance {TASK} --to architecture",
             harv(["advance", TASK, "--to", "architecture", "--owner", "planning-terminal"]),
             "теперь гейт пропускает: требуемые артефакты на месте и зарегистрированы")

    # Оптимистичная блокировка: намеренно неверная ревизия
    complete_stage("architecture")
    snapshot("revision-conflict",
             f"harv advance {TASK} --to backend --expect-revision 999",
             harv(["advance", TASK, "--to", "backend", "--expect-revision", "999",
                   "--owner", "planning-terminal"]),
             "конфликт ревизий: ожидали 999, в файле другая — чужая работа не перезаписывается")

    snapshot("advance-dev", f"harv advance {TASK} --to backend",
             harv(["advance", TASK, "--to", "backend", "--owner", "planning-terminal"]),
             "с корректной ревизией задача уходит в группу dev")

    snapshot("fanout",
             f"harv fanout {TASK} --branch backend --branch frontend --policy strict",
             harv(["fanout", TASK, "--branch", "backend", "--branch", "frontend",
                   "--policy", "strict", "--owner", "dev-terminal"]),
             "fanout создаёт группу ветвей и ставит барьер: при strict соединение "
             "не произойдёт, пока обе ветки не отчитаются. Здесь ветки не "
             "запускались — для их исполнения нужен провайдер LLM, поэтому "
             "барьер честно отказывает")

    snapshot("queues", "harv queues", harv(["queues"]),
             "очереди по стадиям: какой чат что может взять")

    snapshot("validate", "harv validate", harv(["validate"]),
             "проверка целостности .notes/")

    out = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("cli-run.js")
    out.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "title": "Реальный прогон harv",
        "subtitle": "Записан автоматически. Ключи LLM не нужны: harv не ходит в сеть.",
        "task": TASK,
        "steps": steps,
    }
    out.write_text(
        "// Сгенерировано tools/trace-cli.py на реальном прогоне CLI. Не редактировать вручную.\n"
        "window.__CLI_RUN__ = " + json.dumps(payload, ensure_ascii=False, indent=2) + ";\n"
    )
    print(f"\nЗаписано: {out} ({len(steps)} шагов)")

    # harv init регистрирует проект симлинком внутри движка — убираем,
    # чтобы прогон не оставлял следов в репозитории.
    for label in ("personal", "work"):
        link = BACKEND / "projects" / label / project.name
        if link.is_symlink():
            link.unlink()
            print("убран симлинк:", link.relative_to(REPO))

    shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    main()
