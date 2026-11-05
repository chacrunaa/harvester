"""Tests for events/incidents/recovery (TASK-7).

Covers the spec checks: failures land in the canonical journal as incidents,
incidents are listable/resolvable, resolution leaves an event, stale lease is
detectable, and retry after a failed run creates a new run id.
"""
import json
import sys

from test_runtime import BACKEND, RuntimeTestCase

FAKE = BACKEND / "store" / "examples" / "providers" / "fake_agent.py"


class IncidentsTestCase(RuntimeTestCase):
    def journal(self):
        path = self.notes / "history" / "incidents.jsonl"
        if not path.exists():
            return []
        return [json.loads(l) for l in path.read_text(encoding="utf-8").splitlines() if l.strip()]

    def run_provider(self, mode, timeout="30", task="HARV-001", stage="analysis"):
        cmd = f"{sys.executable} {FAKE} {mode}"
        return self.harv("run", task, "--stage", stage, "--owner", "pc",
                         "--provider-cmd", cmd, "--timeout", timeout, "--json")

    def events(self, task="HARV-001"):
        return self.read_json(self.task_json(task)).get("events", [])


class RunnerIncidentTest(IncidentsTestCase):
    def test_invalid_result_recorded_in_journal(self):
        self.assert_ok(self.harv("move", "HARV-001", "--to", "analysis", "--force"))
        self.run_provider("--mode invalid-json")
        incs = self.journal()
        self.assertTrue(incs, "failure must produce an incident")
        inc = incs[-1]
        self.assertEqual(inc["code"], "invalid_structured_result")
        self.assertEqual(inc["severity"], "critical")
        self.assertTrue(inc["run_id"], "run incident carries run_id")
        self.assertTrue(inc["incident_id"].startswith("INC-HARV-001-"))


class HandoffIncidentTest(IncidentsTestCase):
    def test_blocked_handoff_creates_validation_incident(self):
        self.assert_ok(self.harv("move", "HARV-001", "--to", "analysis", "--force"))
        self.harv("advance", "HARV-001", "--to", "architecture", "--owner", "pc")  # fails
        incs = [i for i in self.journal() if i["code"] == "validation_failed"]
        self.assertEqual(len(incs), 1)
        self.assertTrue(incs[0]["links"], "incident links to the validation report")


class ResolveTest(IncidentsTestCase):
    def _make_incident(self):
        self.assert_ok(self.harv("move", "HARV-001", "--to", "analysis", "--force"))
        self.harv("advance", "HARV-001", "--to", "architecture", "--owner", "pc")
        return self.journal()[-1]["incident_id"]

    def test_resolve_sets_status_and_leaves_event(self):
        iid = self._make_incident()
        r = self.harv("incidents", "resolve", iid, "--note", "fixed", "--owner", "pc")
        self.assert_ok(r)
        inc = [i for i in self.journal() if i["incident_id"] == iid][0]
        self.assertEqual(inc["status"], "resolved")
        self.assertEqual(inc["resolution"], "fixed")
        types = [e["type"] for e in self.events()]
        self.assertIn("incident_resolved", types)

    def test_resolve_unknown_incident_errors(self):
        r = self.harv("incidents", "resolve", "INC-NOPE-0001", "--json")
        self.assertEqual(r.returncode, 1)
        self.assertEqual(json.loads(r.stdout)["error"]["code"], "unknown_incident")

    def test_list_filters_by_status(self):
        iid = self._make_incident()
        self.harv("incidents", "resolve", iid, "--owner", "pc")
        # add a second, still-open incident
        self._make_incident()
        open_ids = [i["incident_id"] for i in self.journal() if i["status"] == "open"]
        r = self.harv("incidents", "list", "--status", "open", "--json")
        listed = [i["incident_id"] for i in json.loads(r.stdout)["data"]["incidents"]]
        self.assertEqual(sorted(listed), sorted(open_ids))


class RetryTest(IncidentsTestCase):
    def test_retry_after_failed_run_creates_new_run(self):
        self.assert_ok(self.harv("move", "HARV-001", "--to", "analysis", "--force"))
        r1 = self.run_provider("--mode invalid-json")
        run1 = json.loads(r1.stdout)["error"]["message"].split()[1]
        cmd = f"{sys.executable} {FAKE} --mode success"
        r2 = self.harv("retry", run1, "--provider-cmd", cmd, "--json")
        self.assert_ok(r2, "retry with a good provider should succeed")
        data = json.loads(r2.stdout)["data"]
        self.assertNotEqual(data["run_id"], run1)
        self.assertEqual(data["status"], "succeeded")
        # failed run directory is preserved
        self.assertTrue((self.notes / "history" / "runs" / "HARV-001" / run1).exists())


class StaleLeaseTest(IncidentsTestCase):
    def test_stale_lease_released(self):
        tj = self.task_json("HARV-001")
        task = self.read_json(tj)
        task["runtime"]["lease"] = {
            "owner": "ghost", "agent": "ghost",
            "acquired_at": "2020-01-01T00:00:00+03:00",
            "expires_at": "2020-01-01T01:00:00+03:00",
        }
        self.write_json(tj, task)
        r = self.harv("release", "HARV-001", "--force-stale")
        self.assert_ok(r)
        self.assertIsNone(self.read_json(tj)["runtime"]["lease"])


class CliParserTest(IncidentsTestCase):
    def test_commands_registered(self):
        sys.path.insert(0, str(BACKEND / "app" / "src"))
        from agentforge_notes.cli import build_parser
        self.assertEqual(build_parser().parse_args(["incidents", "list"]).command, "incidents")
        self.assertEqual(build_parser().parse_args(["retry", "RUN-X-001"]).command, "retry")


if __name__ == "__main__":
    import unittest
    unittest.main()
