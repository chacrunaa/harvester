package scripts

import (
	"encoding/json"
	"os"
	"testing"
	"time"
)

// writeTestState writes a PipelineState to the pipeline-state.json in dir.
func writeTestState(t *testing.T, dir string, state PipelineState) {
	t.Helper()
	if err := os.MkdirAll(dir, 0o755); err != nil {
		t.Fatal(err)
	}
	data, _ := json.MarshalIndent(state, "", "  ")
	if err := os.WriteFile(stateFilePath(dir), data, 0o644); err != nil {
		t.Fatal(err)
	}
}

// waitFor polls condition until it is true or deadline passes.
func waitFor(t *testing.T, condition func() bool) {
	t.Helper()
	deadline := time.Now().Add(500 * time.Millisecond)
	for !condition() {
		if time.Now().After(deadline) {
			t.Fatal("condition not met within 500ms")
		}
		time.Sleep(10 * time.Millisecond)
	}
}

// TEST 1 — readState / updateAgentStatus
func TestReadUpdateState(t *testing.T) {
	dir := t.TempDir()

	writeTestState(t, dir, PipelineState{
		TaskID: "TEST-001",
		Phase:  "business",
		Agents: map[string]string{"product-analyst": "waiting"},
	})

	got, err := readState(dir)
	if err != nil {
		t.Fatalf("readState failed: %v", err)
	}
	if got.TaskID != "TEST-001" {
		t.Errorf("task-id mismatch: %q", got.TaskID)
	}
	if got.Phase != "business" {
		t.Errorf("phase mismatch: %q", got.Phase)
	}

	if err := updateAgentStatus(dir, "product-analyst", StatusDone); err != nil {
		t.Fatalf("updateAgentStatus failed: %v", err)
	}
	got2, _ := readState(dir)
	if got2.Agents["product-analyst"] != StatusDone {
		t.Errorf("status not updated, got %q", got2.Agents["product-analyst"])
	}
	if _, err := os.Stat(stateFilePath(dir) + ".tmp"); err == nil {
		t.Error(".tmp file should be removed after atomic write")
	}
}

// TEST 2 — task_id legacy field is also read
func TestReadState_LegacyTaskID(t *testing.T) {
	dir := t.TempDir()
	raw := `{"task_id":"LEGACY-001","phase":"business","agents":{}}`
	must2(t, os.WriteFile(stateFilePath(dir), []byte(raw), 0o644))

	got, _ := readState(dir)
	if got.GetTaskID() != "LEGACY-001" {
		t.Errorf("GetTaskID() should fall back to task_id field, got %q", got.GetTaskID())
	}
}

// TEST 3 — AND-gate: business phase (4 analysts → product-manager)
func TestAndGate_BusinessPhase_PartialNotFired(t *testing.T) {
	dir := t.TempDir()

	var triggered []string
	w := NewWatcher(dir, WatcherCallbacks{
		TriggerAgent: func(agentID, _ string) { triggered = append(triggered, agentID) },
	})

	writeTestState(t, dir, PipelineState{
		TaskID: "TEST-002", Phase: "business",
		Agents: map[string]string{
			"product-analyst": "done", "market-analyst": "done",
			"strategist": "done", "financier": "in-progress",
			"product-manager": "waiting",
		},
	})
	w.onStateChange(dir)

	// Give any goroutine a moment to possibly fire (it shouldn't)
	time.Sleep(50 * time.Millisecond)
	if len(triggered) != 0 {
		t.Errorf("AND-gate should not fire while financier is in-progress, got triggers: %v", triggered)
	}
}

func TestAndGate_BusinessPhase_AllDoneFires(t *testing.T) {
	dir := t.TempDir()

	var triggered []string
	w := NewWatcher(dir, WatcherCallbacks{
		TriggerAgent: func(agentID, _ string) { triggered = append(triggered, agentID) },
	})

	writeTestState(t, dir, PipelineState{
		TaskID: "TEST-002", Phase: "business",
		Agents: map[string]string{
			"product-analyst": "done", "market-analyst": "done",
			"strategist": "done", "financier": "done",
			"product-manager": "waiting",
		},
	})
	w.onStateChange(dir)

	waitFor(t, func() bool { return len(triggered) > 0 })
	if triggered[0] != "business/product-manager" {
		t.Errorf("expected business/product-manager trigger, got %q", triggered[0])
	}
}

// TEST 4 — AND-gate fires only once (idempotent)
func TestAndGate_FiresOnlyOnce(t *testing.T) {
	dir := t.TempDir()

	triggerCount := 0
	w := NewWatcher(dir, WatcherCallbacks{
		TriggerAgent: func(_, _ string) { triggerCount++ },
	})

	state := PipelineState{
		TaskID: "TEST-003", Phase: "business",
		Agents: map[string]string{
			"product-analyst": "done", "market-analyst": "done",
			"strategist": "done", "financier": "done",
			"product-manager": "waiting",
		},
	}
	writeTestState(t, dir, state)
	w.onStateChange(dir)
	waitFor(t, func() bool { return triggerCount > 0 })

	// Second identical state change — gate already fired
	w.onStateChange(dir)
	time.Sleep(100 * time.Millisecond)

	if triggerCount != 1 {
		t.Errorf("AND-gate should fire exactly once, got %d triggers", triggerCount)
	}
}

// TEST 5 — failed agent triggers OnAgentFailed, blocks AND-gate
func TestOnStateChange_FailedAgentDetected(t *testing.T) {
	dir := t.TempDir()

	var failedAgents []string
	var triggered []string
	w := NewWatcher(dir, WatcherCallbacks{
		OnAgentFailed: func(_, _, agent string) { failedAgents = append(failedAgents, agent) },
		TriggerAgent:  func(agentID, _ string) { triggered = append(triggered, agentID) },
	})

	writeTestState(t, dir, PipelineState{
		TaskID: "TEST-004", Phase: "development",
		Agents: map[string]string{
			"dev-lead": "waiting", "backend": "failed",
			"frontend": "in-progress", "reviewers": "waiting",
		},
	})
	w.onStateChange(dir)
	time.Sleep(50 * time.Millisecond)

	if len(failedAgents) == 0 {
		t.Error("OnAgentFailed not called")
	}
	found := false
	for _, a := range failedAgents {
		if a == "backend" {
			found = true
		}
	}
	if !found {
		t.Errorf("expected backend in failed list, got %v", failedAgents)
	}
	// With failures, AND-gate and phase transitions must NOT trigger
	if len(triggered) != 0 {
		t.Errorf("TriggerAgent must not be called when there are failures, got: %v", triggered)
	}
}

// TEST 6 — phase transition: orchestrator done → advance phase + trigger next orchestrator
func TestPhaseTransition_BusinessToSystemic(t *testing.T) {
	dir := t.TempDir()

	var phaseFrom, phaseTo string
	var triggered []string
	w := NewWatcher(dir, WatcherCallbacks{
		OnPhaseAdvanced: func(_, from, to string) { phaseFrom = from; phaseTo = to },
		TriggerAgent:    func(agentID, _ string) { triggered = append(triggered, agentID) },
	})

	writeTestState(t, dir, PipelineState{
		TaskID: "TEST-005", Phase: "business",
		Agents: map[string]string{"product-manager": "done"},
	})
	w.onStateChange(dir)
	waitFor(t, func() bool {
		for _, a := range triggered {
			if a == "systemic/owner" {
				return true
			}
		}
		return false
	})

	if phaseFrom != "business" || phaseTo != "systemic" {
		t.Errorf("expected business→systemic, got %q→%q", phaseFrom, phaseTo)
	}

	// State file on disk reflects new phase
	state, _ := readState(dir)
	if state.Phase != "systemic" {
		t.Errorf("expected phase=systemic in state file, got %q", state.Phase)
	}
}

// TEST 7 — last phase (testing) completes → pipeline complete + office-manager triggered
func TestPhaseTransition_PipelineComplete(t *testing.T) {
	dir := t.TempDir()

	var completedTaskID string
	var triggered []string
	w := NewWatcher(dir, WatcherCallbacks{
		OnPipelineComplete: func(taskID string) { completedTaskID = taskID },
		TriggerAgent:       func(agentID, _ string) { triggered = append(triggered, agentID) },
	})

	writeTestState(t, dir, PipelineState{
		TaskID: "TEST-006", Phase: "testing",
		Agents: map[string]string{"qa-lead": "done"},
	})
	w.onStateChange(dir)
	waitFor(t, func() bool {
		for _, a := range triggered {
			if a == "office-manager" {
				return true
			}
		}
		return false
	})

	if completedTaskID != "TEST-006" {
		t.Errorf("expected completedTaskID=TEST-006, got %q", completedTaskID)
	}
}

func must2(t *testing.T, err error) {
	t.Helper()
	if err != nil {
		t.Fatal(err)
	}
}
