package lib

import (
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"
	"regexp"
	"strings"
)

var skillRefRe = regexp.MustCompile("`(skills/[^`]+\\.md)`")

// RouteMap is the parsed content of an agent's .route-map.json file.
type RouteMap struct {
	Inputs        []RouteInput  `json:"inputs"`
	Outputs       []RouteOutput `json:"outputs"`
	Routing       []RoutingRule `json:"routing"`
	CodeOutputDir string        `json:"codeOutputDir"`
}

// RouteInput describes a file the agent expects to receive as input.
type RouteInput struct {
	Name     string `json:"name"`
	Path     string `json:"path"`
	Required bool   `json:"required"`
}

// RouteOutput describes a file the agent is expected to emit.
type RouteOutput struct {
	Name string `json:"name"`
	Path string `json:"path"`
}

// RoutingRule copies a file from → to after the agent finishes.
type RoutingRule struct {
	From string `json:"from"`
	To   string `json:"to"`
}

// LoadRouteMap reads and parses a .route-map.json file.
func LoadRouteMap(path string) (*RouteMap, error) {
	data, err := os.ReadFile(path)
	if err != nil {
		return nil, fmt.Errorf("route-map not found: %s", path)
	}
	var rm RouteMap
	if err := json.Unmarshal(data, &rm); err != nil {
		return nil, fmt.Errorf("route-map parse %s: %w", path, err)
	}
	return &rm, nil
}

// BuildContext assembles the system and user prompts for an agent LLM call.
//
//   - agentID      — "business/product-analyst"
//   - taskID       — "CTD-001"
//   - projectRoot  — absolute path to the target project
//   - harvestAiDir — absolute path to harvester's .ai/ (agent prompts, skills)
func BuildContext(agentID, taskID, projectRoot, harvestAiDir string, routeMap *RouteMap) (system, user string, err error) {
	agentMdPath := filepath.Join(harvestAiDir, "agents", agentID+".md")
	promptBytes, err := os.ReadFile(agentMdPath)
	if err != nil {
		return "", "", fmt.Errorf("agent prompt not found: %s", agentMdPath)
	}
	agentPrompt := string(promptBytes)

	skills := loadSkills(agentPrompt, harvestAiDir)
	system = buildSystemPrompt(agentPrompt, skills)

	type inputEntry struct {
		name    string
		content string
		missing bool
	}
	var inputs []inputEntry
	var missingRequired []string

	for _, inp := range routeMap.Inputs {
		absPath := filepath.Join(projectRoot, inp.Path)
		data, readErr := os.ReadFile(absPath)
		missing := readErr != nil
		if missing && inp.Required {
			missingRequired = append(missingRequired, inp.Path)
		}
		entry := inputEntry{name: inp.Name, missing: missing}
		if !missing {
			entry.content = string(data)
		}
		inputs = append(inputs, entry)
	}

	if len(missingRequired) > 0 {
		return "", "", fmt.Errorf("required inputs missing: %s", strings.Join(missingRequired, ", "))
	}

	// Build user message
	taskLabel := taskID
	if taskLabel == "" {
		taskLabel = "—"
	}
	var sections []string
	sections = append(sections, "## Контекст задачи\ntask-id: "+taskLabel)

	var inputSec strings.Builder
	inputSec.WriteString("## Входящие файлы\n")
	hasInputs := false
	for _, inp := range inputs {
		if inp.missing {
			continue
		}
		hasInputs = true
		inputSec.WriteString("\n### " + inp.name + "\n```\n" + inp.content + "\n```")
	}
	if hasInputs {
		sections = append(sections, inputSec.String())
	}

	var outList, outExamples strings.Builder
	for _, o := range routeMap.Outputs {
		fmt.Fprintf(&outList, "- `%s`\n", o.Name)
		fmt.Fprintf(&outExamples, "<file name=%q>\n{содержимое файла}\n</file>\n\n", o.Name)
	}

	codeSection := ""
	if routeMap.CodeOutputDir != "" {
		codeSection = "\n## Файлы кода\n\n" +
			"Помимо обязательных файлов выше, запишите **все файлы исходного кода** тоже в XML-блоки.\n" +
			"Путь в атрибуте `name` — относительно директории `" + routeMap.CodeOutputDir + "/` проекта.\n\n" +
			"Создавай столько файлов сколько нужно. Пиши полный рабочий код — не заглушки.\n"
	}

	sections = append(sections,
		"## Инструкция по формату ответа\n\n"+
			"Запишите каждый выходной файл в XML-теге. Записывайте только готовые файлы.\n\n"+
			"Ожидаемые файлы:\n"+outList.String()+
			"\nФормат:\n"+outExamples.String()+
			codeSection+
			"\nЕсли нужно задать уточняющие вопросы пользователю — используйте выходной файл `qna` (qna.json).\n"+
			"Формат содержимого:\n"+
			`{"questions": [{"id": 1, "question": "Ваш вопрос?", "answer": null}]}`,
	)

	user = strings.Join(sections, "\n\n")
	return system, user, nil
}

type skill struct {
	ref     string
	content string
}

func loadSkills(agentPrompt, aiDir string) []skill {
	var skills []skill
	for _, m := range skillRefRe.FindAllStringSubmatch(agentPrompt, -1) {
		ref := m[1]
		data, err := os.ReadFile(filepath.Join(aiDir, ref))
		if err != nil {
			continue
		}
		skills = append(skills, skill{ref: ref, content: string(data)})
	}
	return skills
}

func buildSystemPrompt(agentPrompt string, skills []skill) string {
	if len(skills) == 0 {
		return agentPrompt
	}
	var sb strings.Builder
	sb.WriteString(agentPrompt)
	for _, s := range skills {
		sb.WriteString("\n---\n## Инструкция: " + s.ref + "\n\n" + s.content)
	}
	return sb.String()
}
