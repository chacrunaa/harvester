"""Tests for validating handoff (TASK-6, `harv advance`).

Covers the spec's required checks: forward transitions need registered outputs,
backward/loop transitions do not, queue drift / unknown transition / stale
revision block, and `done` leaves the task in no queue. Reuses RuntimeTestCase.
"""
import json

from test_runtime import RuntimeTestCase


class HandoffTestCase(RuntimeTestCase):
    def advance(self, task, to, *extra):
        return self.harv("advance", task, "--to", to, "--owner", "tester", "--json", *extra)

    def force_to(self, task, stage):
        # position a task at an arbitrary stage (updates queue + runtime)
        self.assert_ok(self.harv("move", task, "--to", stage, "--force"), f"force-> {stage}")

    def make_output(self, task, rel, art_type=None):
        """Create a required output file; register it when it is an artifact."""
        if rel.startswith("history/"):
            path = self.notes / rel
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(f"# {rel}\n", encoding="utf-8")
            if art_type:
                self.assert_ok(self.harv("add-artifact", task, "--type", art_type,
                                         "--path", rel, "--owner", "tester"))
        else:  # project-root output (documentations/**), not registerable
            path = self.tmp / rel
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(f"# {rel}\n", encoding="utf-8")

    def report(self, result):
        return json.loads(result.stdout)


class HappyPathTest(HandoffTestCase):
    def test_owner_to_analysis(self):  # intake -> analysis (no registerable outputs)
        r = self.advance("HARV-001", "analysis")
        self.assert_ok(r)
        data = self.report(r)["data"]
        self.assertTrue(data["ok"])
        self.assertEqual(data["status"], "ready_for_next_stage")
        self.assertEqual(self.read_json(self.task_json("HARV-001"))["runtime"]["current_stage"],
                         "analysis")
        self.assert_ok(self.validate(), "runtime stays valid")

    def test_analysis_to_architecture_with_registered_outputs(self):
        self.force_to("HARV-001", "analysis")
        self.make_output("HARV-001", "history/briefs/analyst/HARV-001.analysis-brief.md", "brief")
        self.make_output("HARV-001", "history/specifications/HARV-001.developer-spec.md", "specification")
        self.make_output("HARV-001", "history/memory/analyst/HARV-001.md", "memory")
        r = self.advance("HARV-001", "architecture")
        self.assert_ok(r, "all outputs present+registered -> advance ok")
        self.assert_ok(self.validate())

    def test_review_accepted_to_done_clears_queue(self):
        self.force_to("HARV-001", "review")
        self.make_output("HARV-001", "history/reports/reviewer/HARV-001.review-report.md", "report")
        self.make_output("HARV-001", "history/memory/reviewer/HARV-001.md", "memory")
        r = self.advance("HARV-001", "done")
        self.assert_ok(r)
        task = self.read_json(self.task_json("HARV-001"))
        self.assertEqual(task["runtime"]["current_stage"], "done")
        self.assertIsNone(task["backlog"]["queue_link"])
        # not present in any stage queue
        for qf in self.notes.glob("tasks/backlog/**/queue.json"):
            ids = [i["task_id"] for i in self.read_json(qf).get("items", [])]
            self.assertNotIn("HARV-001", ids, f"still queued in {qf}")
        self.assert_ok(self.validate())

    def test_review_code_adjustment_backward_needs_no_outputs(self):
        self.force_to("HARV-001", "review")
        r = self.advance("HARV-001", "backend")  # needs_adjustment, backward
        self.assert_ok(r, "backward transition needs no outputs")
        self.assertEqual(self.report(r)["data"]["status"], "needs_adjustment")


class BlockingTest(HandoffTestCase):
    def test_missing_outputs_collects_all(self):
        self.force_to("HARV-001", "analysis")
        r = self.advance("HARV-001", "architecture")
        self.assertEqual(r.returncode, 1)
        rep = self.report(r)
        self.assertFalse(rep["ok"])
        codes = [e["code"] for e in rep["errors"]]
        self.assertEqual(codes.count("required_output_missing"), 3, "all 3 reported, not just first")

    def test_file_exists_but_not_registered(self):
        self.force_to("HARV-001", "analysis")
        # create files without registering them
        self.make_output("HARV-001", "history/briefs/analyst/HARV-001.analysis-brief.md")
        self.make_output("HARV-001", "history/specifications/HARV-001.developer-spec.md")
        self.make_output("HARV-001", "history/memory/analyst/HARV-001.md")
        r = self.advance("HARV-001", "architecture")
        self.assertEqual(r.returncode, 1)
        codes = [e["code"] for e in self.report(r)["errors"]]
        self.assertTrue(all(c == "artifact_not_registered" for c in codes))
        self.assertEqual(len(codes), 3)

    def test_queue_drift_blocks(self):
        # remove the task from its current-stage queue, then try to advance
        qf = self.owner_queue()
        q = self.read_json(qf)
        q["items"] = [i for i in q["items"] if i["task_id"] != "HARV-001"]
        self.write_json(qf, q)
        r = self.advance("HARV-001", "analysis")
        self.assertEqual(r.returncode, 1)
        self.assertIn("queue_drift", [e["code"] for e in self.report(r)["errors"]])

    def test_unknown_transition_blocks(self):
        r = self.advance("HARV-001", "review")  # no edge owner -> review
        self.assertEqual(r.returncode, 1)
        self.assertIn("transition_not_allowed", [e["code"] for e in self.report(r)["errors"]])

    def test_stale_revision_blocks(self):
        rev = self.read_json(self.task_json("HARV-001"))["runtime"]["revision"]
        r = self.advance("HARV-001", "analysis", "--expect-revision", str(rev + 5))
        self.assertEqual(r.returncode, 1)
        self.assertIn("stale_revision", [e["code"] for e in self.report(r)["errors"]])

    def test_failed_handoff_writes_durable_report(self):
        self.force_to("HARV-001", "analysis")
        self.advance("HARV-001", "architecture")  # fails
        reports = list((self.notes / "history" / "handoffs" / "HARV-001").glob("EVT-*.json"))
        self.assertTrue(reports, "failed handoff must persist a report")
        rep = self.read_json(reports[-1])
        self.assertFalse(rep["ok"])
        self.assertTrue(rep["errors"])


class CliParserTest(HandoffTestCase):
    def test_advance_registered(self):
        import sys
        from test_runtime import BACKEND
        sys.path.insert(0, str(BACKEND / "app" / "src"))
        from agentforge_notes.cli import build_parser
        args = build_parser().parse_args(["advance", "HARV-001", "--to", "done"])
        self.assertEqual(args.command, "advance")


if __name__ == "__main__":
    import unittest
    unittest.main()
