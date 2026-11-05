package scripts

import (
	"fmt"
	"log"
	"path/filepath"
	"strings"

	"harvester/scripts/lib"
)

const (
	StatusInProgress = "in-progress"
	StatusDone       = "done"
	StatusFailed     = "failed"
	StatusQnaPending = "qna-pending"
)

// RunOptions configures a single RunAgent invocation.
type RunOptions struct {
	HarvestAiDir string     // harvester's .ai/ directory (agent prompts, skills, rules)
	AIDir        string     // target project's .ai/ directory
	TaskID       string
	DryRun       bool
	LLM          lib.Config // provider + key + model
	// LLMCallFn overrides lib.Call — used in tests to inject a mock LLM.
	LLMCallFn func(lib.Config, string, string, lib.CallOpts) (string, error)
}

// RunResult is the outcome of RunAgent.
type RunResult struct {
	Status string // "done" | "qna-pending" | "failed"
	Error  string
}

// RunAgent executes the full agent cycle:
//
//  1. Mark agent in-progress
//  2. Load route-map
//  3. Build LLM context (system + user prompts)
//  4. Call LLM
//  5. Parse response → file map
//  6. Write output files atomically
//  7. Check qna for unanswered questions
//  8. Apply routing rules
//  9. Spawn docs-writer (async)
//  10. Mark agent done
func RunAgent(agentID string, opts RunOptions) RunResult {
	aiDir := opts.AIDir
	projectRoot := filepath.Dir(aiDir)
	agentName := agentBaseName(agentID)
	logDir := filepath.Join(aiDir, "chats", "dialogs")

	fail := func(err error) RunResult {
		log.Printf("[runner] %s: %v", agentID, err)
		if !opts.DryRun {
			_ = updateAgentStatus(aiDir, agentName, StatusFailed)
		}
		return RunResult{Status: StatusFailed, Error: err.Error()}
	}

	if !opts.DryRun {
		_ = updateAgentStatus(aiDir, agentName, StatusInProgress)
	}

	// Load route-map
	routeMapPath := filepath.Join(opts.HarvestAiDir, "agents", agentID+".route-map.json")
	routeMap, err := lib.LoadRouteMap(routeMapPath)
	if err != nil {
		return fail(fmt.Errorf("cannot load route-map: %w", err))
	}

	// Build LLM context
	system, user, err := lib.BuildContext(agentID, opts.TaskID, projectRoot, opts.HarvestAiDir, routeMap)
	if err != nil {
		return fail(fmt.Errorf("context build failed: %w", err))
	}

	// Call LLM
	callFn := opts.LLMCallFn
	if callFn == nil {
		callFn = lib.Call
	}
	rawResponse, err := callFn(opts.LLM, system, user, lib.CallOpts{
		TaskID: opts.TaskID,
		Agent:  agentID,
		LogDir: logDir,
	})
	if err != nil {
		return fail(fmt.Errorf("LLM call failed: %w", err))
	}

	// Parse files from response
	parsedFiles := lib.ParseFiles(rawResponse)
	if len(parsedFiles) == 0 {
		return fail(fmt.Errorf("LLM response contained no <file> blocks"))
	}

	// Write output files
	if !opts.DryRun {
		fixedNames := make(map[string]bool, len(routeMap.Outputs))
		for _, output := range routeMap.Outputs {
			fixedNames[output.Name] = true
			content, ok := parsedFiles[output.Name]
			if !ok {
				continue
			}
			absPath := filepath.Join(projectRoot, output.Path)
			if writeErr := lib.WriteAtomic(absPath, content); writeErr != nil {
				return fail(fmt.Errorf("write %s: %w", output.Name, writeErr))
			}
			log.Printf("[runner] %s: wrote %s → %s", agentID, output.Name, output.Path)
		}

		if routeMap.CodeOutputDir != "" {
			codeDir := filepath.Join(projectRoot, routeMap.CodeOutputDir)
			for name, content := range parsedFiles {
				if fixedNames[name] {
					continue
				}
				absPath := filepath.Join(codeDir, name)
				if writeErr := lib.WriteAtomic(absPath, content); writeErr != nil {
					log.Printf("[runner] %s: write code %s: %v", agentID, name, writeErr)
					continue
				}
				log.Printf("[runner] %s: wrote code %s → %s/%s", agentID, name, routeMap.CodeOutputDir, name)
			}
		}
	}

	// QnA check
	for _, output := range routeMap.Outputs {
		if !isQnaOutput(output) {
			continue
		}
		content, ok := parsedFiles[output.Name]
		if !ok {
			continue
		}
		if lib.HasUnansweredQuestions(content) {
			log.Printf("[runner] %s: qna-pending", agentID)
			return RunResult{Status: StatusQnaPending}
		}
	}

	// Apply routing rules
	if !opts.DryRun {
		for _, r := range lib.ApplyRouting(routeMap.Routing, projectRoot) {
			if r.OK {
				log.Printf("[runner] routed: %s → %s", r.From, r.To)
			}
		}
	}

	// Docs writer — fire-and-forget
	if !opts.DryRun && opts.TaskID != "" {
		go lib.WriteDocs(agentID, opts.TaskID, aiDir, projectRoot, logDir, opts.LLM, opts.HarvestAiDir)
	}

	// Mark done
	if !opts.DryRun {
		_ = updateAgentStatus(aiDir, agentName, StatusDone)
	}
	log.Printf("[runner] %s: done", agentID)
	return RunResult{Status: StatusDone}
}

func agentBaseName(agentID string) string {
	if idx := strings.LastIndex(agentID, "/"); idx >= 0 {
		return agentID[idx+1:]
	}
	return agentID
}

func isQnaOutput(o lib.RouteOutput) bool {
	return o.Name == "qna" || o.Name == "qna.json" || strings.HasSuffix(o.Path, "qna.json")
}
