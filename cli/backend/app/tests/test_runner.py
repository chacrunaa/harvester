"""Tests for the sub-agent runner protocol (TASK-5, `harv run`).

Reuses the RuntimeTestCase scaffold: a temp copy of store/examples/notes driven
through the real CLI as a subprocess. A fake provider script stands in for an
agent runner and is parameterised through --mode.
"""
import json

from test_runtime import BACKEND, RuntimeTestCase

FAKE = BACKEND / "store" / "examples" / "providers" / "fake_agent.py"


class RunnerTestCase(RuntimeTestCase):
    def run_harv(self, *extra, mode="success", timeout="30", task="HARV-001",
                 stage="analysis"):
        import sys
        provider_cmd = f"{sys.executable} {FAKE} {mode}"
        return self.harv(
            "run", task, "--stage", stage, "--owner", "planning-console",
            "--provider-cmd", provider_cmd, "--timeout", timeout, "--json", *extra)

    def payload(self, result):
        return json.loads(result.stdout)

    def runs_dir(self, task="HARV-001"):
        return self.notes / "history" / "runs" / task

    def incidents(self, task="HARV-001"):
        # canonical journal lives at history/incidents.jsonl (TASK-7)
        path = self.notes / "history" / "incidents.jsonl"
        if not path.exists():
            return []
        items = [json.loads(l) for l in path.read_text(encoding="utf-8").splitlines() if l.strip()]
        return [i for i in items if i.get("task_id") == task]


class SuccessTest(RunnerTestCase):
    def test_success_registers_artifacts_and_stays_valid(self):  # C1
        r = self.run_harv(mode="--mode success")
        self.assert_ok(r, "success run must exit 0")
        data = self.payload(r)["data"]
        self.assertEqual(data["status"], "succeeded")
        rd = self.runs_dir() / data["run_id"]
        for name in ("request.json", "result.json", "metadata.json", "raw-output.txt"):
            self.assertTrue((rd / name).exists(), f"{name} must be written")
        # declared artifacts are registered in task.json
        task = self.read_json(self.task_json("HARV-001"))
        self.assertIn("history/briefs/analyst/HARV-001.analysis-brief.md",
                      task["artifacts"]["briefs"])
        self.assert_ok(self.validate(), "runtime must stay valid after run")

    def test_raw_output_is_not_result(self):
        r = self.run_harv(mode="--mode success")
        data = self.payload(r)["data"]
        result = self.read_json(self.runs_dir() / data["run_id"] / "result.json")
        self.assertEqual(result["schema_version"], 1)
        self.assertEqual(result["status"], "succeeded")


class InvalidResultTest(RunnerTestCase):
    def test_invalid_json_fails_with_incident(self):  # C2 / C6
        r = self.run_harv(mode="--mode invalid-json")
        self.assertEqual(r.returncode, 1, "invalid result must fail")
        err = json.loads(r.stdout)["error"]
        self.assertEqual(err["code"], "invalid_structured_result")
        codes = [i["code"] for i in self.incidents()]
        self.assertIn("invalid_structured_result", codes)
        self.assert_ok(self.validate(), "runtime stays valid after failed run")


class TimeoutTest(RunnerTestCase):
    def test_timeout_records_metadata_and_incident(self):  # C3
        r = self.run_harv(mode="--mode timeout --sleep 5", timeout="1")
        self.assertEqual(r.returncode, 1)
        codes = [i["code"] for i in self.incidents()]
        self.assertIn("runner_timeout", codes)
        # run-level timed_out lives in metadata, not result.status
        run_id = json.loads(r.stdout)["error"]["message"].split()[1]
        meta = self.read_json(self.runs_dir() / run_id / "metadata.json")
        self.assertTrue(meta["timed_out"])


class PartialArtifactsTest(RunnerTestCase):
    def test_undeclared_artifact_blocks(self):  # C4
        r = self.run_harv(mode="--mode artifact-not-declared")
        self.assertEqual(r.returncode, 1, "undeclared artifacts must block")
        err = json.loads(r.stdout)["error"]
        self.assertEqual(err["code"], "partial_artifacts")
        msgs = [i["message"] for i in self.incidents()]
        self.assertTrue(any("not declared" in m for m in msgs))


class RetryTest(RunnerTestCase):
    def test_retry_creates_new_run_without_overwriting(self):  # C5
        r1 = self.run_harv(mode="--mode invalid-json")
        run1 = json.loads(r1.stdout)["error"]["message"].split()[1]
        rd1 = self.runs_dir() / run1
        before = (rd1 / "result.json").read_text(encoding="utf-8")

        r2 = self.run_harv("--retry-of", run1, mode="--mode success")
        self.assert_ok(r2)
        run2 = json.loads(r2.stdout)["data"]["run_id"]
        self.assertNotEqual(run1, run2)
        # previous run dir untouched
        self.assertEqual((rd1 / "result.json").read_text(encoding="utf-8"), before)
        # new run records previous_run_id
        meta2 = self.read_json(self.runs_dir() / run2 / "metadata.json")
        self.assertEqual(meta2["previous_run_id"], run1)


class CliParserTest(RunnerTestCase):
    def test_run_command_registered(self):  # C7
        import sys
        sys.path.insert(0, str(BACKEND / "app" / "src"))
        from agentforge_notes.cli import build_parser
        args = build_parser().parse_args(["run", "HARV-001", "--provider-cmd", "x"])
        self.assertEqual(args.command, "run")
        self.assertEqual(args.task_id, "HARV-001")


if __name__ == "__main__":
    import unittest
    unittest.main()
