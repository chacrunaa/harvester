package lib

import (
	"os"
	"path/filepath"
	"strings"
	"testing"
)

// setupContextFixtures creates a minimal harvestAiDir + projectRoot with
// agent prompt, skill, route-map, and one required input file.
func setupContextFixtures(t *testing.T) (harvestAiDir, projectRoot string, rm *RouteMap) {
	t.Helper()
	harvestAiDir = t.TempDir()
	projectRoot = t.TempDir()

	// Agent prompt referencing a skill via backtick syntax
	agentDir := filepath.Join(harvestAiDir, "agents", "business")
	mustMkdir(t, agentDir)
	agentPrompt := "# product-analyst\n\nИнструкции: `skills/business/01-product-brief.md`\n\n## Роль\nАнализирует продукт."
	mustWriteFile(t, filepath.Join(agentDir, "product-analyst.md"), agentPrompt)

	// Skill referenced from prompt
	skillDir := filepath.Join(harvestAiDir, "skills", "business")
	mustMkdir(t, skillDir)
	mustWriteFile(t, filepath.Join(skillDir, "01-product-brief.md"), "# Product Brief\nОпиши проблему, продукт, уникальность.")

	// Required input in project tree
	inputDir := filepath.Join(projectRoot, ".ai", "chats", "business")
	mustMkdir(t, inputDir)
	mustWriteFile(t, filepath.Join(inputDir, "cross-brief.md"), "# Cross Brief\nПродукт: TODO-приложение для iOS.")

	rm = &RouteMap{
		Inputs: []RouteInput{
			{Name: "cross-brief", Path: ".ai/chats/business/cross-brief.md", Required: true},
			{Name: "experience", Path: ".ai/chats/business/product-analyst/experience.md", Required: false},
		},
		Outputs: []RouteOutput{
			{Name: "report.md", Path: ".ai/chats/business/product-analyst/report.md"},
			{Name: "qna.json", Path: ".ai/chats/business/product-analyst/qna.json"},
		},
		Routing: []RoutingRule{
			{From: ".ai/chats/business/product-analyst/report.md", To: ".ai/chats/business/product-manager/reports/product-analyst.md"},
		},
	}
	return
}

func TestBuildContext_SystemContainsAgentRole(t *testing.T) {
	harvestAiDir, projectRoot, rm := setupContextFixtures(t)
	system, _, err := BuildContext("business/product-analyst", "TEST-100", projectRoot, harvestAiDir, rm)
	if err != nil {
		t.Fatalf("BuildContext failed: %v", err)
	}
	if !strings.Contains(system, "product-analyst") {
		t.Error("system prompt missing agent role")
	}
}

func TestBuildContext_SystemIncludesSkill(t *testing.T) {
	harvestAiDir, projectRoot, rm := setupContextFixtures(t)
	system, _, err := BuildContext("business/product-analyst", "TEST-100", projectRoot, harvestAiDir, rm)
	if err != nil {
		t.Fatalf("BuildContext failed: %v", err)
	}
	if !strings.Contains(system, "Product Brief") {
		t.Error("system prompt missing skill content from 01-product-brief.md")
	}
}

func TestBuildContext_UserContainsInputFile(t *testing.T) {
	harvestAiDir, projectRoot, rm := setupContextFixtures(t)
	_, user, err := BuildContext("business/product-analyst", "TEST-100", projectRoot, harvestAiDir, rm)
	if err != nil {
		t.Fatalf("BuildContext failed: %v", err)
	}
	if !strings.Contains(user, "TODO-приложение") {
		t.Error("user prompt missing cross-brief.md content")
	}
}

func TestBuildContext_UserContainsTaskID(t *testing.T) {
	harvestAiDir, projectRoot, rm := setupContextFixtures(t)
	_, user, err := BuildContext("business/product-analyst", "TEST-100", projectRoot, harvestAiDir, rm)
	if err != nil {
		t.Fatalf("BuildContext failed: %v", err)
	}
	if !strings.Contains(user, "TEST-100") {
		t.Error("user prompt missing task-id")
	}
}

func TestBuildContext_UserContainsOutputFormat(t *testing.T) {
	harvestAiDir, projectRoot, rm := setupContextFixtures(t)
	_, user, err := BuildContext("business/product-analyst", "TEST-100", projectRoot, harvestAiDir, rm)
	if err != nil {
		t.Fatalf("BuildContext failed: %v", err)
	}
	if !strings.Contains(user, `<file name="report.md">`) {
		t.Error("user prompt missing output format example")
	}
}

func TestBuildContext_MissingRequiredInput(t *testing.T) {
	harvestAiDir, projectRoot, rm := setupContextFixtures(t)
	rm.Inputs = []RouteInput{
		{Name: "nope", Path: ".ai/nope.md", Required: true},
	}
	_, _, err := BuildContext("business/product-analyst", "TEST-100", projectRoot, harvestAiDir, rm)
	if err == nil {
		t.Error("expected error for missing required input")
	}
}

func TestBuildContext_MissingOptionalInputIgnored(t *testing.T) {
	harvestAiDir, projectRoot, rm := setupContextFixtures(t)
	// experience.md is optional and does not exist — should not error
	_, _, err := BuildContext("business/product-analyst", "TEST-100", projectRoot, harvestAiDir, rm)
	if err != nil {
		t.Errorf("unexpected error with missing optional input: %v", err)
	}
}

// helpers

func mustMkdir(t *testing.T, path string) {
	t.Helper()
	if err := os.MkdirAll(path, 0o755); err != nil {
		t.Fatal(err)
	}
}

func mustWriteFile(t *testing.T, path, content string) {
	t.Helper()
	if err := os.WriteFile(path, []byte(content), 0o644); err != nil {
		t.Fatal(err)
	}
}
