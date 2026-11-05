"""End-to-end tests for the .notes runtime.

Each test copies the canonical template (store/examples/notes) into a temporary
.notes/ directory and drives the real CLI as a subprocess, so find_notes_root
discovers the temp runtime via cwd. This exercises the exact code path users hit
and asserts the TASK-1 invariants.
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[2]
TEMPLATE = BACKEND / "store" / "examples" / "notes"
SRC = BACKEND / "app" / "src"


class RuntimeTestCase(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp, ignore_errors=True)
        self.notes = self.tmp / ".notes"
        shutil.copytree(TEMPLATE, self.notes)

    # --- helpers -----------------------------------------------------------
    def harv(self, *argv):
        env = dict(os.environ, PYTHONPATH=str(SRC))
        return subprocess.run(
            [sys.executable, "-m", "agentforge_notes", *argv],
            cwd=self.tmp,
            env=env,
            capture_output=True,
            text=True,
        )

    def assert_ok(self, result, msg=""):
        self.assertEqual(result.returncode, 0, f"{msg}\nstdout:{result.stdout}\nstderr:{result.stderr}")

    def validate(self):
        return self.harv("validate")

    def backlog(self, *parts):
        return self.notes.joinpath("tasks", "backlog", *parts)

    def read_json(self, path):
        return json.loads(Path(path).read_text(encoding="utf-8"))

    def write_json(self, path, data):
        Path(path).write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    def task_json(self, task_id):
        return self.notes / "history" / "tasks" / task_id / "task.json"

    def owner_queue(self):
        return self.backlog("plan", "stages", "intake", "queue.json")


class TemplateInvariantsTest(RuntimeTestCase):
    def test_clean_template_validates(self):
        self.assert_ok(self.validate(), "clean template must validate")

    def test_demo_tasks_status(self):
        expected = {
            "HARV-001": "intake",
            "HARV-002": "analysis",
            "HARV-003": "backend",
        }
        for task_id, stage in expected.items():
            r = self.harv("status", task_id)
            self.assert_ok(r, task_id)
            self.assertEqual(json.loads(r.stdout)["stage"], stage)


class CreateTest(RuntimeTestCase):
    def test_create_zero_padded_and_queued(self):
        r = self.harv("create", "Новая демо-задача", "--epic", "demo-discovery")
        self.assert_ok(r)
        self.assertIn("HARV-004", r.stdout)  # zero-padded, not HARV-4

        queue = self.read_json(self.owner_queue())
        ids = [it["task_id"] for it in queue["items"]]
        self.assertIn("HARV-004", ids)

        self.assert_ok(self.validate(), "runtime must stay valid after create")


class HappyPathTest(RuntimeTestCase):
    def test_take_move_add_artifact_keeps_runtime_valid(self):
        # HARV-001 starts new in intake.
        self.assert_ok(self.harv("take", "HARV-001", "--stage", "intake", "--owner", "planning"))
        self.assert_ok(self.validate(), "valid after take")

        rev_before = self.read_json(self.task_json("HARV-001"))["runtime"]["revision"]
        events_before = len(self.read_json(self.task_json("HARV-001"))["events"])

        self.assert_ok(self.harv("move", "HARV-001", "--to", "analysis", "--owner", "planning"))
        self.assert_ok(self.validate(), "valid after move")

        task = self.read_json(self.task_json("HARV-001"))
        self.assertEqual(task["runtime"]["current_stage"], "analysis")
        self.assertGreater(task["runtime"]["revision"], rev_before, "revision must grow")
        self.assertGreaterEqual(len(task["events"]), events_before, "events must not be dropped")
        self.assertEqual(
            task["backlog"]["queue_link"],
            "../../../tasks/backlog/plan/stages/analysis/queue.json",
        )

        # exactly one queue holds it
        in_owner = any(i["task_id"] == "HARV-001" for i in self.read_json(self.owner_queue())["items"])
        self.assertFalse(in_owner, "must have left the owner queue")


class EdgeCaseTest(RuntimeTestCase):
    def assert_validate_fails(self, needle):
        r = self.validate()
        self.assertEqual(r.returncode, 1, f"validate should fail\n{r.stdout}")
        self.assertIn(needle, r.stdout, r.stdout)

    def test_double_queue_detected(self):
        # also enqueue HARV-001 into the analysis queue
        aq_path = self.backlog("plan", "stages", "analysis", "queue.json")
        aq = self.read_json(aq_path)
        aq["items"].append({"task_id": "HARV-001", "task_link": "x", "priority": 1})
        self.write_json(aq_path, aq)
        self.assert_validate_fails("queued in")

    def test_orphan_queue_item_detected(self):
        q = self.read_json(self.owner_queue())
        q["items"].append({"task_id": "HARV-999", "task_link": "x", "priority": 1})
        self.write_json(self.owner_queue(), q)
        self.assert_validate_fails("orphan queue item")

    def test_unknown_stage_detected(self):
        task = self.read_json(self.task_json("HARV-001"))
        task["runtime"]["current_stage"] = "9-nonexistent"
        self.write_json(self.task_json("HARV-001"), task)
        self.assert_validate_fails("invalid current_stage")

    def test_status_out_of_catalog_detected(self):
        task = self.read_json(self.task_json("HARV-001"))
        task["runtime"]["status"] = "totally-made-up"
        self.write_json(self.task_json("HARV-001"), task)
        self.assert_validate_fails("status_catalog")

    def test_missing_source_detected(self):
        (self.notes / "history" / "tasks" / "HARV-001" / "source.txt").unlink()
        self.assert_validate_fails("source file missing")

    def test_expired_lease_warns_not_errors(self):
        task = self.read_json(self.task_json("HARV-001"))
        task["runtime"]["lease"] = {
            "owner": "planning",
            "agent": "product-owner",
            "acquired_at": "2000-01-01T00:00:00+03:00",
            "expires_at": "2000-01-01T01:00:00+03:00",
        }
        self.write_json(self.task_json("HARV-001"), task)
        r = self.validate()
        self.assert_ok(r, "expired lease must not break runtime")
        self.assertIn("lease expired", r.stdout)


def jdata(result):
    return json.loads(result.stdout)


class ReadCommandsTest(RuntimeTestCase):
    def test_list_filter_and_json(self):
        r = self.harv("list", "--stage", "analysis", "--json")
        self.assert_ok(r)
        env = jdata(r)
        self.assertTrue(env["ok"])
        self.assertEqual(env["command"], "list")
        ids = [t["task_id"] for t in env["data"]["tasks"]]
        self.assertEqual(ids, ["HARV-002"])

    def test_queues_json(self):
        env = jdata(self.harv("queues", "--stage", "intake", "--json"))
        q = env["data"]["queues"][0]
        self.assertEqual(q["stage"], "intake")
        self.assertEqual([i["task_id"] for i in q["items"]], ["HARV-001"])

    def test_artifacts_existence(self):
        env = jdata(self.harv("artifacts", "HARV-003", "--json"))
        briefs = env["data"]["artifacts"]["briefs"]
        self.assertTrue(briefs and briefs[0]["exists"])

    def test_events_json(self):
        env = jdata(self.harv("events", "HARV-003", "--json"))
        self.assertTrue(any(e["type"] == "task_created" for e in env["data"]["events"]))


class MoveGateTest(RuntimeTestCase):
    def test_forward_move_with_outputs_ok(self):
        # intake outputs (task.json, source.txt) exist -> allowed
        r = self.harv("move", "HARV-001", "--to", "analysis", "--owner", "planning")
        self.assert_ok(r)

    def test_transition_not_allowed(self):
        env = jdata(self.harv("move", "HARV-002", "--to", "test", "--owner", "x", "--json"))
        self.assertFalse(env["ok"])
        self.assertEqual(env["error"]["code"], "transition_not_allowed")

    def test_required_output_missing(self):
        # HARV-002 at analysis lacks analysis briefs/specs -> forward move refused
        env = jdata(self.harv("move", "HARV-002", "--to", "architecture", "--owner", "x", "--json"))
        self.assertFalse(env["ok"])
        self.assertEqual(env["error"]["code"], "required_output_missing")
        self.assertIsNotNone(env["error"]["next_action"])

    def test_force_bypasses_gate(self):
        self.assert_ok(self.harv("move", "HARV-002", "--to", "architecture", "--owner", "x", "--force"))


class ReleaseTest(RuntimeTestCase):
    def test_force_stale_refuses_active_lease(self):
        self.assert_ok(self.harv("take", "HARV-001", "--stage", "intake", "--owner", "planning"))
        env = jdata(self.harv("release", "HARV-001", "--force-stale", "--json"))
        self.assertFalse(env["ok"])
        self.assertEqual(env["error"]["code"], "lease_active")

    def test_force_stale_releases_expired_lease(self):
        task = self.read_json(self.task_json("HARV-001"))
        task["runtime"]["lease"] = {
            "owner": "ghost", "agent": "product-owner",
            "acquired_at": "2000-01-01T00:00:00+03:00",
            "expires_at": "2000-01-01T01:00:00+03:00",
        }
        self.write_json(self.task_json("HARV-001"), task)
        self.assert_ok(self.harv("release", "HARV-001", "--force-stale"))
        after = self.read_json(self.task_json("HARV-001"))
        self.assertIsNone(after["runtime"]["lease"])
        self.assertTrue(any(e["type"] == "task_released" for e in after["events"]))


class QuestionsTest(RuntimeTestCase):
    def test_lifecycle(self):
        add = jdata(self.harv("questions", "add", "HARV-001", "--question", "Объём?", "--json"))
        qid = add["data"]["question"]["id"]
        self.assertEqual(qid, "Q-HARV-001-001")

        self.assert_ok(self.harv("questions", "answer", "HARV-001", "--id", qid, "--answer", "10k"))
        self.assert_ok(self.harv("questions", "close", "HARV-001", "--id", qid))

        lst = jdata(self.harv("questions", "list", "HARV-001", "--json"))
        q = lst["data"]["questions"][0]
        self.assertEqual(q["status"], "closed")
        self.assertEqual(q["answer"], "10k")
        self.assert_ok(self.validate(), "runtime valid after questions")

    def test_answer_unknown_id(self):
        env = jdata(self.harv("questions", "answer", "HARV-001", "--id", "Q-X", "--answer", "a", "--json"))
        self.assertEqual(env["error"]["code"], "question_not_found")


class RepairTest(RuntimeTestCase):
    def test_repair_fixes_queue_drift(self):
        # remove HARV-001 from its queue -> missing queue item drift
        q = self.read_json(self.owner_queue())
        q["items"] = [i for i in q["items"] if i["task_id"] != "HARV-001"]
        self.write_json(self.owner_queue(), q)
        self.assertEqual(self.validate().returncode, 1)

        dry = jdata(self.harv("repair", "--json"))
        self.assertFalse(dry["data"]["applied"])
        self.assertTrue(any(a["action"] == "add_missing_queue_item" for a in dry["data"]["actions"]))

        self.assert_ok(self.harv("repair", "--apply"))
        self.assert_ok(self.validate(), "repair must restore a valid runtime")

    def test_repair_removes_orphan(self):
        q = self.read_json(self.owner_queue())
        q["items"].append({"task_id": "HARV-999", "task_link": "x", "priority": 1})
        self.write_json(self.owner_queue(), q)
        self.assert_ok(self.harv("repair", "--apply"))
        ids = [i["task_id"] for i in self.read_json(self.owner_queue())["items"]]
        self.assertNotIn("HARV-999", ids)


class JsonContractTest(RuntimeTestCase):
    def test_validate_json_ok(self):
        env = jdata(self.harv("validate", "--json"))
        self.assertTrue(env["ok"])
        self.assertEqual(env["command"], "validate")
        self.assertTrue(env["data"]["ok"])

    def test_status_json_envelope(self):
        env = jdata(self.harv("status", "HARV-001", "--json"))
        self.assertTrue(env["ok"])
        self.assertEqual(env["task_id"], "HARV-001")
        self.assertEqual(env["data"]["stage"], "intake")


class FanoutExitValidationTest(RuntimeTestCase):
    """validate safeguards backing the fan-out auto-exit (TASK-8): groups must be
    contiguous and every fan-out group must have a following group to exit into."""

    def _codes(self):
        return [f["code"] for f in jdata(self.harv("validate", "--json"))["data"]["findings"]]

    def test_non_contiguous_group_flagged(self):
        stages = self.read_json(self.backlog("stages.json"))
        for st in stages["stages"]:
            if st["id"] == "review":  # makes `dev` reappear after `testing`
                st["group"] = "dev"
        self.write_json(self.backlog("stages.json"), stages)
        self.assertIn("group_not_contiguous", self._codes())

    def test_fanout_group_without_exit_flagged(self):
        stages = self.read_json(self.backlog("stages.json"))
        stages["fanout_groups"] = ["dev", "review"]  # review is the last block
        self.write_json(self.backlog("stages.json"), stages)
        self.assertIn("fanout_group_no_exit", self._codes())


if __name__ == "__main__":
    unittest.main()
