package scripts

import (
	"encoding/json"
	"os"
	"path/filepath"
	"strings"
	"testing"

	"harvester/scripts/lib"
)

// setupRunnerFixtures builds a minimal temp workspace for RunAgent tests:
//
//	root/
//	  harvester-ai/  ← HarvestAiDir
//	    agents/business/product-analyst.md
//	    agents/business/product-analyst.route-map.json
//	    skills/business/01-product-brief.md
//	  project/       ← projectRoot
//	    .ai/          ← AIDir
//	      pipeline-state.json
//	      chats/business/cross-brief.md   (required input)
func setupRunnerFixtures(t *testing.T) (harvestAiDir, aiDir string) {
	t.Helper()
	root := t.TempDir()
	harvestAiDir = filepath.Join(root, "harvester-ai")
	projectRoot := filepath.Join(root, "project")
	aiDir = filepath.Join(projectRoot, ".ai")

	for _, d := range []string{
		filepath.Join(harvestAiDir, "agents", "business"),
		filepath.Join(harvestAiDir, "skills", "business"),
		filepath.Join(aiDir, "chats", "business", "product-analyst"),
		filepath.Join(aiDir, "chats", "business", "product-manager", "reports"),
		filepath.Join(aiDir, "chats", "dialogs"),
	} {
		if err := os.MkdirAll(d, 0o755); err != nil {
			t.Fatal(err)
		}
	}

	agentMd := "# product-analyst\n\nИнструкции: `skills/business/01-product-brief.md`\n\n## Роль\nАнализирует продукт."
	must(t, os.WriteFile(filepath.Join(harvestAiDir, "agents", "business", "product-analyst.md"), []byte(agentMd), 0o644))
	must(t, os.WriteFile(filepath.Join(harvestAiDir, "skills", "business", "01-product-brief.md"), []byte("# Product Brief"), 0o644))

	routeMap := map[string]interface{}{
		"inputs": []map[string]interface{}{
			{"name": "cross-brief", "path": ".ai/chats/business/cross-brief.md", "required": true},
		},
		"outputs": []map[string]interface{}{
			{"name": "report.md", "path": ".ai/chats/business/product-analyst/report.md"},
			{"name": "qna.json", "path": ".ai/chats/business/product-analyst/qna.json"},
		},
		"routing": []map[string]interface{}{
			{"from": ".ai/chats/business/product-analyst/report.md", "to": ".ai/chats/business/product-manager/reports/product-analyst.md"},
		},
	}
	rmData, _ := json.Marshal(routeMap)
	must(t, os.WriteFile(filepath.Join(harvestAiDir, "agents", "business", "product-analyst.route-map.json"), rmData, 0o644))

	must(t, os.WriteFile(filepath.Join(aiDir, "chats", "business", "cross-brief.md"), []byte("# Cross Brief\nПродукт: TODO-app."), 0o644))

	state := PipelineState{TaskID: "TEST-100", Phase: "business", Agents: map[string]string{"product-analyst": "waiting"}}
	stateData, _ := json.MarshalIndent(state, "", "  ")
	must(t, os.WriteFile(stateFilePath(aiDir), stateData, 0o644))

	return harvestAiDir, aiDir
}

func must(t *testing.T, err error) {
	t.Helper()
	if err != nil {
		t.Fatal(err)
	}
}

// TEST 1 — done flow
func TestRunAgent_Done(t *testing.T) {
	harvestAiDir, aiDir := setupRunnerFixtures(t)

	mockLLM := func(_ lib.Config, _, _ string, _ lib.CallOpts) (string, error) {
		return `<file name="report.md">
# Product Analysis Report
Продукт: TODO-app. MVP: базовые задачи + локальное хранение.
</file>`, nil
	}

	result := RunAgent("business/product-analyst", RunOptions{
		HarvestAiDir: harvestAiDir,
		AIDir:        aiDir,
		TaskID:       "TEST-100",
		LLMCallFn:    mockLLM,
	})

	if result.Status != StatusDone {
		t.Fatalf("expected status=done, got %q: %s", result.Status, result.Error)
	}

	// Output file written
	reportPath := filepath.Join(aiDir, "chats", "business", "product-analyst", "report.md")
	data, err := os.ReadFile(reportPath)
	if err != nil {
		t.Fatalf("report.md not written: %v", err)
	}
	if !strings.Contains(string(data), "TODO-app") {
		t.Error("report.md content mismatch")
	}

	// Routing applied: report copied to product-manager/reports/
	routedPath := filepath.Join(aiDir, "chats", "business", "product-manager", "reports", "product-analyst.md")
	if _, err := os.Stat(routedPath); err != nil {
		t.Error("report.md not routed to product-manager/reports/")
	}

	// pipeline-state updated
	state, err := readState(aiDir)
	if err != nil {
		t.Fatalf("cannot read state: %v", err)
	}
	if state.Agents["product-analyst"] != StatusDone {
		t.Errorf("expected agent=done in state, got %q", state.Agents["product-analyst"])
	}
}

// TEST 2 — qna-pending flow
func TestRunAgent_QnaPending(t *testing.T) {
	harvestAiDir, aiDir := setupRunnerFixtures(t)

	mockLLM := func(_ lib.Config, _, _ string, _ lib.CallOpts) (string, error) {
		return `<file name="qna.json">
{"questions": [{"id": 1, "question": "Кто целевая аудитория?", "answer": null}]}
</file>`, nil
	}

	result := RunAgent("business/product-analyst", RunOptions{
		HarvestAiDir: harvestAiDir,
		AIDir:        aiDir,
		TaskID:       "TEST-100",
		LLMCallFn:    mockLLM,
	})

	if result.Status != StatusQnaPending {
		t.Errorf("expected status=qna-pending, got %q", result.Status)
	}

	// qna.json written to disk
	qnaPath := filepath.Join(aiDir, "chats", "business", "product-analyst", "qna.json")
	if _, err := os.Stat(qnaPath); err != nil {
		t.Error("qna.json not written to disk")
	}

	// Agent stays in-progress (not done/failed)
	state, _ := readState(aiDir)
	if state.Agents["product-analyst"] != StatusInProgress {
		t.Errorf("agent should remain in-progress on qna-pending, got %q", state.Agents["product-analyst"])
	}
}

// TEST 3 — failed flow: LLM returns no <file> blocks
func TestRunAgent_FailedNoFileBlocks(t *testing.T) {
	harvestAiDir, aiDir := setupRunnerFixtures(t)

	mockLLM := func(_ lib.Config, _, _ string, _ lib.CallOpts) (string, error) {
		return "Я не знаю что ответить.", nil
	}

	result := RunAgent("business/product-analyst", RunOptions{
		HarvestAiDir: harvestAiDir,
		AIDir:        aiDir,
		TaskID:       "TEST-100",
		LLMCallFn:    mockLLM,
	})

	if result.Status != StatusFailed {
		t.Errorf("expected status=failed when LLM returns no <file> blocks, got %q", result.Status)
	}

	state, _ := readState(aiDir)
	if state.Agents["product-analyst"] != StatusFailed {
		t.Errorf("expected agent=failed in state, got %q", state.Agents["product-analyst"])
	}
}
