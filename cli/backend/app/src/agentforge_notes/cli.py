import argparse
import sys

from .output import CommandError, emit_error

ARTIFACT_KEYS = {
    "brief",
    "specification",
    "report",
    "memory",
    "chat",
    "question",
}


def build_parser():
    parser = argparse.ArgumentParser(prog="notes", description="AgentForge .notes runtime helper")

    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--json", action="store_true", help="машиночитаемый вывод {ok, command, data/error}")

    sub = parser.add_subparsers(dest="command", required=True)

    def add(name, **kwargs):
        return sub.add_parser(name, parents=[common], **kwargs)

    p = add("status")
    p.add_argument("task_id")

    p = add("list", help="список задач из индекса")
    p.add_argument("--stage")
    p.add_argument("--group")
    p.add_argument("--status")
    p.add_argument("--epic")

    p = add("queues", help="содержимое очередей стадий")
    p.add_argument("--group")
    p.add_argument("--stage")

    p = add("artifacts", help="индекс артефактов задачи с проверкой файлов")
    p.add_argument("task_id")

    p = add("events", help="события задачи")
    p.add_argument("task_id")

    p = add("take")
    p.add_argument("task_id")
    p.add_argument("--stage", required=True)
    p.add_argument("--owner", required=True)
    p.add_argument("--ttl-minutes", type=int)

    p = add("release", help="освободить lease задачи")
    p.add_argument("task_id")
    p.add_argument("--owner", default="manual")
    p.add_argument("--force-stale", action="store_true", help="снять только истёкший lease")

    p = add("move")
    p.add_argument("task_id")
    p.add_argument("--to", required=True)
    p.add_argument("--status")
    p.add_argument("--owner", default="manual")
    p.add_argument("--priority", type=int, default=100)
    p.add_argument("--force", action="store_true", help="обойти проверку transition/required outputs")

    p = add("advance", help="validating handoff на следующую стадию (gatekeeper)")
    p.add_argument("task_id")
    p.add_argument("--to", required=True)
    p.add_argument("--status")
    p.add_argument("--owner", default="manual")
    p.add_argument("--priority", type=int, default=100)
    p.add_argument("--expect-revision", dest="expect_revision", type=int,
                   help="optimistic concurrency: ожидаемый runtime.revision")

    p = add("add-artifact")
    p.add_argument("task_id")
    p.add_argument("--type", required=True, choices=sorted(ARTIFACT_KEYS))
    p.add_argument("--path", required=True)
    p.add_argument("--question")
    p.add_argument("--owner", default="manual")

    p = add("questions", help="работа с вопросами задачи")
    qsub = p.add_subparsers(dest="questions_command", required=True)
    qp = qsub.add_parser("list", parents=[common])
    qp.add_argument("task_id")
    qp = qsub.add_parser("add", parents=[common])
    qp.add_argument("task_id")
    qp.add_argument("--question", required=True)
    qp.add_argument("--owner", default="manual")
    qp = qsub.add_parser("answer", parents=[common])
    qp.add_argument("task_id")
    qp.add_argument("--id", required=True)
    qp.add_argument("--answer", required=True)
    qp.add_argument("--owner", default="manual")
    qp = qsub.add_parser("close", parents=[common])
    qp.add_argument("task_id")
    qp.add_argument("--id", required=True)
    qp.add_argument("--owner", default="manual")

    p = add("incidents", help="журнал инцидентов и recovery")
    p.add_argument("--task")
    p.add_argument("--status")
    isub = p.add_subparsers(dest="incidents_command")
    ip = isub.add_parser("list", parents=[common])
    ip.add_argument("--task")
    ip.add_argument("--status")
    ip = isub.add_parser("show", parents=[common])
    ip.add_argument("incident_id")
    ip = isub.add_parser("resolve", parents=[common])
    ip.add_argument("incident_id")
    ip.add_argument("--note")
    ip.add_argument("--status", help="resolved|acknowledged|ignored (default resolved)")
    ip.add_argument("--owner", default="manual")

    p = add("retry", help="повторить failed run новым run_id")
    p.add_argument("run_id")
    p.add_argument("--provider-cmd", dest="provider_cmd",
                   help="команда внешнего runner (или env HARV_PROVIDER_CMD)")
    p.add_argument("--timeout", type=int)

    p = add("create")
    p.add_argument("description", help="описание задачи (используется как название и источник)")
    p.add_argument("--epic")
    p.add_argument("--task-id")

    p = add("init", help="инициализировать .notes/ в целевом проекте")
    p.add_argument("path", help="путь к целевому проекту")
    p.add_argument("--force", action="store_true", help="перезаписать существующий .notes/")
    kind = p.add_mutually_exclusive_group(required=True)
    kind.add_argument("--work", dest="kind", action="store_const", const="work",
                      help="рабочий проект → projects/work/")
    kind.add_argument("--personal", dest="kind", action="store_const", const="personal",
                      help="личный проект → projects/personal/")
    p.add_argument("--backend", help="каталог backend-кода (по умолчанию автодетект)")
    p.add_argument("--ui", help="каталог UI/frontend-кода (по умолчанию автодетект)")
    p.add_argument("--docs", help="каталог документации (по умолчанию автодетект)")

    p = add("use", help="выбрать активный проект (напр. work/my-service)")
    p.add_argument("project", help="метка проекта из projects/ (напр. work/my-service)")

    for group_cmd in ("planning", "dev", "testing", "review"):
        add(group_cmd, help=f"вывести инструкции группы {group_cmd}")

    p = add("run", help="запустить sub-agent через provider adapter (scripted run)")
    p.add_argument("task_id")
    p.add_argument("--stage", help="стадия (по умолчанию runtime.current_stage)")
    p.add_argument("--owner", default="manual")
    p.add_argument("--provider", default="command", help="имя provider adapter")
    p.add_argument("--provider-cmd", dest="provider_cmd",
                   help="команда внешнего runner (или env HARV_PROVIDER_CMD)")
    p.add_argument("--timeout", type=int, default=3600, help="timeout в секундах")
    p.add_argument("--retry-of", dest="retry_of", help="run_id предыдущей попытки")

    p = add("fanout", help="параллельный fan-out веток группы development + join (TASK-8)")
    p.add_argument("task_id")
    p.add_argument("--branch", action="append", dest="branches", metavar="STAGE_ID",
                   help="ветка (стадия); повторяемо. По умолчанию — стадии группы development")
    p.add_argument("--optional", action="append", dest="optional", metavar="STAGE_ID",
                   default=[], help="пометить ветку необязательной; повторяемо")
    p.add_argument("--policy", choices=["strict", "best-effort"], default="strict")
    p.add_argument("--owner", default="manual")
    p.add_argument("--provider", default="command", help="имя provider adapter")
    p.add_argument("--provider-cmd", dest="provider_cmd",
                   help="команда внешнего runner по умолчанию (или env HARV_PROVIDER_CMD)")
    p.add_argument("--branch-cmd", action="append", dest="branch_cmd", default=[],
                   metavar="STAGE_ID=CMD", help="per-branch provider override; повторяемо")
    p.add_argument("--timeout", type=int, default=3600, help="per-run timeout в секундах")

    p = add("validate")
    p.add_argument("--task", help="проверить только одну задачу")

    p = add("repair", help="безопасные исправления queue/lease drift")
    p.add_argument("--apply", action="store_true", help="выполнить правки (по умолчанию dry-run)")

    add("sync-index")

    return parser


def dispatch(args):
    if args.command == "init":
        from .init_cmd import cmd_init
        cmd_init(args)
        return

    if args.command == "use":
        from .project_cmd import cmd_use
        cmd_use(args)
        return

    if args.command in ("planning", "dev", "testing", "review"):
        from .project_cmd import cmd_group
        cmd_group(args)
        return

    from . import commands

    handlers = {
        "status": commands.cmd_status,
        "list": commands.cmd_list,
        "queues": commands.cmd_queues,
        "artifacts": commands.cmd_artifacts,
        "events": commands.cmd_events,
        "take": commands.cmd_take,
        "release": commands.cmd_release,
        "move": commands.cmd_move,
        "advance": commands.cmd_advance,
        "add-artifact": commands.cmd_add_artifact,
        "questions": commands.cmd_questions,
        "incidents": commands.cmd_incidents,
        "run": commands.cmd_run,
        "fanout": commands.cmd_fanout,
        "retry": commands.cmd_retry,
        "create": commands.cmd_create,
        "validate": commands.cmd_validate,
        "repair": commands.cmd_repair,
        "sync-index": commands.cmd_sync_index,
    }
    handlers[args.command](args)


def main():
    parser = build_parser()
    args = parser.parse_args()
    try:
        dispatch(args)
    except CommandError as exc:
        emit_error(args, args.command, exc)
        sys.exit(1)


if __name__ == "__main__":
    main()
