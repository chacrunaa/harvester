package scripts

import (
	"encoding/json"
	"os"
	"path/filepath"
	"sync"
)

// PipelineState mirrors pipeline-state.json.
type PipelineState struct {
	TaskID       string            `json:"task-id,omitempty"`
	TaskIDLegacy string            `json:"task_id,omitempty"`
	Phase        string            `json:"phase,omitempty"`
	Agents       map[string]string `json:"agents"`
}

func (s *PipelineState) GetTaskID() string {
	if s.TaskID != "" {
		return s.TaskID
	}
	return s.TaskIDLegacy
}

var (
	muMu    sync.Mutex
	fileMus = map[string]*sync.Mutex{}
)

func fileMutex(path string) *sync.Mutex {
	muMu.Lock()
	defer muMu.Unlock()
	if m, ok := fileMus[path]; ok {
		return m
	}
	m := &sync.Mutex{}
	fileMus[path] = m
	return m
}

func readState(aiDir string) (*PipelineState, error) {
	data, err := os.ReadFile(stateFilePath(aiDir))
	if err != nil {
		return nil, err
	}
	var s PipelineState
	if err := json.Unmarshal(data, &s); err != nil {
		return nil, err
	}
	return &s, nil
}

func updateAgentStatus(aiDir, agentName, status string) error {
	path := stateFilePath(aiDir)
	mu := fileMutex(path)
	mu.Lock()
	defer mu.Unlock()

	data, err := os.ReadFile(path)
	if err != nil {
		return err
	}
	var s PipelineState
	if err := json.Unmarshal(data, &s); err != nil {
		return err
	}
	if s.Agents == nil {
		s.Agents = make(map[string]string)
	}
	s.Agents[agentName] = status

	out, err := json.MarshalIndent(s, "", "  ")
	if err != nil {
		return err
	}
	if err := os.MkdirAll(filepath.Dir(path), 0o755); err != nil {
		return err
	}
	tmp := path + ".tmp"
	if err := os.WriteFile(tmp, out, 0o644); err != nil {
		return err
	}
	return os.Rename(tmp, path)
}

func stateFilePath(aiDir string) string {
	return filepath.Join(aiDir, "pipeline-state.json")
}
