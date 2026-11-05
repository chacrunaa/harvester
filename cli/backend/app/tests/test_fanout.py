"""Tests for parallel fan-out of the development group (TASK-8, `harv fanout`).

Reuses the RuntimeTestCase scaffold: a temp copy of store/examples/notes driven
through the real CLI. The fake provider (`fake_agent.py`) stands in for branch
sub-agents; per-branch behaviour is selected with `--branch-cmd STAGE=CMD`.
"""
import json
import sys
import time

from test_runtime import BACKEND, RuntimeTestCase

FAKE = BACKEND / "store" / "examples" / "providers" / "fake_agent.py"


def provider_cmd(mode, sleep=None, work=None):
    cmd = f"{sys.executable} {FAKE} --mode {mode}"
    if sleep is not None:
        cmd += f" --sleep {sleep}"
    if work is not None:
        cmd += f" --work {work}"
    return cmd


class FanoutTestCase(RuntimeTestCase):
    TASK = "HARV-003"  # template task already sitting in the development group

    def fanout(self, *extra):
        return self.harv("fanout", self.TASK, "--owner", "dev-console", "--json", *extra)

    def runs_dir(self):
        return self.notes / "history" / "runs" / self.TASK

    def incident_codes(self):
        path = self.notes / "history" / "incidents.jsonl"
        if not path.exists():
            return []
        return [json.loads(l)["code"] for l in path.read_text(encoding="utf-8").splitlines() if l.strip()]

    def manifest(self, data):
        return self.read_json(self.runs_dir() / data["group_run_id"] / "group-run.json")

    def place_at_integration(self):
        # integration is the group's exit stage (has -> test).
        self.assert_ok(self.harv("move", self.TASK, "--to", "integration",
                                 "--owner", "x", "--force"))


class ParallelJoinTest(FanoutTestCase):
    def test_two_branches_run_parallel_and_join(self):  # C1 + C6
        # Each branch simulates ~1s of work. If the two ran sequentially the
        # command would take ~2s; parallel dispatch keeps wall-clock near the
        # single-branch duration. We assert the overlap directly below.
        WORK = 1.0
        started = time.monotonic()
        r = self.fanout("--branch", "backend", "--branch", "frontend",
                        "--provider-cmd", provider_cmd("success", work=WORK))
        wall = time.monotonic() - started
        self.assert_ok(r)
        data = json.loads(r.stdout)["data"]
        self.assertTrue(data["ok"])
        self.assertEqual({b["status"] for b in data["branches"]}, {"succeeded"})

        # both branches got their own run dir
        for b in data["branches"]:
            self.assertTrue((self.runs_dir() / b["run_id"]).exists())
        self.assertEqual(len({b["run_id"] for b in data["branches"]}), 2)

        # Parallelism proof: sum of per-branch durations is ~2*WORK, but the two
        # ran concurrently so the whole command finished in well under that sum.
        durations = [self.read_json(self.runs_dir() / b["run_id"] / "metadata.json")["duration_seconds"]
                     for b in data["branches"]]
        self.assertEqual(len(durations), 2)
        self.assertTrue(all(d >= WORK for d in durations),
                        f"each branch should really do ~{WORK}s of work: {durations}")
        self.assertLess(wall, sum(durations),
                        f"wall-clock {wall:.2f}s must be below the sequential sum "
                        f"{sum(durations):.2f}s — branches did not run in parallel")

        m = self.manifest(data)
        self.assertTrue(m["joined"] and m["ok"])

        # C6: artifacts of both branches registered, runtime stays valid
        self.assert_ok(self.validate(), "task.json must stay valid after parallel fan-out")
        task = self.read_json(self.task_json(self.TASK))
        self.assertIn("history/reports/developer/backend/HARV-003.backend-report.md",
                      task["artifacts"]["reports"])
        self.assertIn("history/reports/developer/frontend/HARV-003.frontend-report.md",
                      task["artifacts"]["reports"])


class TimeoutTest(FanoutTestCase):
    def test_slow_branch_times_out_without_hanging_join(self):  # C2
        # frontend sleeps past the per-run timeout; the join must still converge.
        r = self.fanout("--branch", "backend", "--branch", "frontend",
                        "--provider-cmd", provider_cmd("success"),
                        "--branch-cmd", f"frontend={provider_cmd('timeout', sleep=5)}",
                        "--timeout", "1")
        # required frontend timed out -> strict join blocked (command exits 1).
        # The test reaching this assertion at all proves the join did not hang.
        self.assertEqual(r.returncode, 1)
        codes = self.incident_codes()
        self.assertIn("runner_timeout", codes)
        self.assertIn("fanout_join_blocked", codes)
        # the fast branch still succeeded and the slow one is terminal (failed),
        # never left pending/running on the manifest
        grp = sorted(self.runs_dir().glob("GRP-*"))[-1]
        manifest = self.read_json(grp / "group-run.json")
        self.assertTrue(manifest["joined"])
        statuses = {b["stage_id"]: b["status"] for b in manifest["branches"]}
        self.assertEqual(statuses["backend"], "succeeded")
        self.assertEqual(statuses["frontend"], "failed")


class StrictPolicyTest(FanoutTestCase):
    def test_failed_required_blocks_join_and_advance(self):  # C3
        self.place_at_integration()
        r = self.fanout("--branch", "backend", "--branch", "integration",
                        "--provider-cmd", provider_cmd("success"),
                        "--branch-cmd", f"backend={provider_cmd('failed')}")
        self.assertEqual(r.returncode, 1, "strict: failed required branch must block")
        codes = self.incident_codes()
        self.assertIn("fanout_branch_failed", codes)
        self.assertIn("fanout_join_blocked", codes)

        # advance out of the development group must be refused
        adv = self.harv("advance", self.TASK, "--to", "test", "--owner", "x", "--json")
        self.assertEqual(adv.returncode, 1)
        report = json.loads(adv.stdout)
        self.assertIn("fanout_join_blocked", [e["code"] for e in report["errors"]])


class BestEffortPolicyTest(FanoutTestCase):
    def test_optional_failure_passes_join_and_advance(self):  # C4
        self.place_at_integration()
        r = self.fanout(
            "--policy", "best-effort",
            "--branch", "backend", "--branch", "integration",
            "--branch", "frontend", "--optional", "frontend",
            "--provider-cmd", provider_cmd("success"),
            "--branch-cmd", f"frontend={provider_cmd('failed')}")
        self.assert_ok(r, "best-effort: optional failure must still join")
        data = json.loads(r.stdout)["data"]
        self.assertTrue(data["ok"])
        self.assertIn("fanout_partial", self.incident_codes())

        # required branches (incl. integration) succeeded -> handoff allowed
        adv = self.harv("advance", self.TASK, "--to", "test", "--owner", "x", "--json")
        self.assert_ok(adv, "advance must pass once best-effort join converged")


class AutoExitTest(FanoutTestCase):
    """The engine derives the fan-out group exit from pipeline order, so a task
    may leave its group from the anchor stage even when no explicit transition to
    the next group is declared (TASK-8 group auto-exit)."""

    def test_advance_from_anchor_without_explicit_transition(self):
        # HARV-003 sits on `backend`, whose transitions do NOT include -> test.
        self.assertEqual(
            self.read_json(self.task_json(self.TASK))["runtime"]["current_stage"], "backend")
        stages = self.read_json(self.backlog("stages.json"))
        backend = next(s for s in stages["stages"] if s["id"] == "backend")
        self.assertNotIn("test", {t["next_stage"] for t in backend["transitions"].values()})

        # A converged fan-out over the group...
        r = self.fanout("--branch", "backend", "--branch", "frontend",
                        "--provider-cmd", provider_cmd("success"))
        self.assert_ok(r)
        self.assertTrue(json.loads(r.stdout)["data"]["ok"])

        # ...lets advance synthesize backend -> test (next group's entry stage).
        adv = self.harv("advance", self.TASK, "--to", "test", "--owner", "x", "--json")
        self.assert_ok(adv, "auto-exit must allow leaving the group from the anchor")
        self.assertEqual(
            self.read_json(self.task_json(self.TASK))["runtime"]["current_stage"], "test")
        self.assert_ok(self.validate())

    def test_auto_exit_blocked_without_converged_fanout(self):
        # No fan-out run yet -> the anchor has no path to test, advance refused.
        adv = self.harv("advance", self.TASK, "--to", "test", "--owner", "x", "--json")
        self.assertEqual(adv.returncode, 1)
        codes = [e["code"] for e in json.loads(adv.stdout)["errors"]]
        self.assertIn("transition_not_allowed", codes)


class RetryIsolationTest(FanoutTestCase):
    def test_retry_failed_branch_keeps_siblings(self):  # C5
        r = self.fanout(
            "--policy", "best-effort",
            "--branch", "backend", "--branch", "frontend",
            "--optional", "frontend",
            "--provider-cmd", provider_cmd("success"),
            "--branch-cmd", f"frontend={provider_cmd('failed')}")
        self.assert_ok(r)
        data = json.loads(r.stdout)["data"]
        runs = {b["stage_id"]: b["run_id"] for b in data["branches"]}
        backend_before = (self.runs_dir() / runs["backend"] / "result.json").read_text(encoding="utf-8")

        rr = self.harv("retry", runs["frontend"],
                       "--provider-cmd", provider_cmd("success"), "--json")
        self.assert_ok(rr, "retry of the failed branch must succeed")
        run2 = json.loads(rr.stdout)["data"]["run_id"]
        self.assertNotEqual(run2, runs["frontend"])
        # sibling backend run untouched
        self.assertEqual(
            (self.runs_dir() / runs["backend"] / "result.json").read_text(encoding="utf-8"),
            backend_before)


class CliParserTest(FanoutTestCase):
    def test_fanout_registered(self):
        sys.path.insert(0, str(BACKEND / "app" / "src"))
        from agentforge_notes.cli import build_parser
        args = build_parser().parse_args(
            ["fanout", "HARV-003", "--branch", "backend"])
        self.assertEqual(args.command, "fanout")
        self.assertEqual(args.branches, ["backend"])


if __name__ == "__main__":
    import unittest
    unittest.main()
