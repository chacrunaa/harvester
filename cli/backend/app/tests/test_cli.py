import unittest

from agentforge_notes.cli import build_parser


class CliParserTest(unittest.TestCase):
    def test_validate_command_is_registered(self):
        args = build_parser().parse_args(["validate"])
        self.assertEqual(args.command, "validate")

    def test_known_commands_parse(self):
        for argv in (
            ["status", "HARV-001"],
            ["list", "--stage", "analysis"],
            ["queues", "--group", "plan"],
            ["artifacts", "HARV-001"],
            ["events", "HARV-001"],
            ["create", "topic"],
            ["take", "HARV-001", "--stage", "intake", "--owner", "me"],
            ["release", "HARV-001", "--force-stale"],
            ["move", "HARV-001", "--to", "analysis", "--force"],
            ["add-artifact", "HARV-001", "--type", "report", "--path", "x.md"],
            ["repair", "--apply"],
            ["sync-index"],
        ):
            with self.subTest(argv=argv):
                args = build_parser().parse_args(argv)
                self.assertEqual(args.command, argv[0])

    def test_questions_subcommands_parse(self):
        for sub in (
            ["list", "HARV-001"],
            ["add", "HARV-001", "--question", "q"],
            ["answer", "HARV-001", "--id", "Q-HARV-001-001", "--answer", "a"],
            ["close", "HARV-001", "--id", "Q-HARV-001-001"],
        ):
            with self.subTest(sub=sub):
                args = build_parser().parse_args(["questions", *sub])
                self.assertEqual(args.command, "questions")
                self.assertEqual(args.questions_command, sub[0])


if __name__ == "__main__":
    unittest.main()
