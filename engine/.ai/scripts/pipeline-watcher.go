package scripts

import (
	"encoding/json"
	"log"
	"os"
	"path/filepath"
	"strings"
	"sync"
	"time"

	"github.com/fsnotify/fsnotify"
)

// WatcherCallbacks are plugged in by the backend to react to pipeline events.
// All callbacks are optional — nil callbacks are silently ignored.
type WatcherCallbacks struct {
	TriggerAgent       func(agentID, taskID string)
	OnStateChanged     func(state *PipelineState)
	OnAgentFailed      func(taskID, phase, agent string)
	OnQnaPending       func(qnaPath string)
	OnPhaseAdvanced    func(taskID, from, to string)
	OnPipelineComplete func(taskID string)
	OnFileChanged      func(path string)
}

var phaseOrder = []string{"business", "systemic", "development", "testing"}

var phaseOrchestrators = map[string]string{
	"business":    "product-manager",
	"systemic":    "owner",
	"development": "dev-lead",
	"testing":     "qa-lead",
}

type andGate struct {
	phase   string
	agents  []string
	trigger string
}

var andGates = []andGate{
	{
		phase:   "business",
		agents:  []string{"product-analyst", "market-analyst", "strategist", "financier"},
		trigger: "business/product-manager",
	},
	{
		phase:   "development",
		agents:  []string{"backend", "frontend"},
		trigger: "development/reviewers",
	},
}

// PipelineWatcher monitors pipeline-state.json and chats/, implements AND-gates and phase transitions.
type PipelineWatcher struct {
	mu         sync.Mutex
	aiDir      string
	fsw        *fsnotify.Watcher
	cb         WatcherCallbacks
	firedGates map[string]bool
}

// NewWatcher creates a watcher for the given aiDir with the provided callbacks.
func NewWatcher(aiDir string, cb WatcherCallbacks) *PipelineWatcher {
	return &PipelineWatcher{
		aiDir:      aiDir,
		cb:         cb,
		firedGates: make(map[string]bool),
	}
}

// Restart stops the current watcher and starts a new one for aiDir.
func (w *PipelineWatcher) Restart(aiDir string) {
	w.mu.Lock()
	if w.fsw != nil {
		_ = w.fsw.Close()
		w.fsw = nil
	}
	w.aiDir = aiDir
	w.firedGates = make(map[string]bool)
	w.mu.Unlock()

	if aiDir == "" {
		return
	}
	w.Start()
}

// Start begins watching the configured aiDir.
func (w *PipelineWatcher) Start() {
	aiDir := w.aiDir
	if aiDir == "" {
		return
	}

	fsw, err := fsnotify.NewWatcher()
	if err != nil {
		log.Printf("[watcher] create error: %v", err)
		return
	}
	w.mu.Lock()
	w.fsw = fsw
	w.mu.Unlock()

	stateFile := stateFilePath(aiDir)
	chatsDir := filepath.Join(aiDir, "chats")

	_ = fsw.Add(aiDir)
	_ = fsw.Add(stateFile)
	if err := os.MkdirAll(chatsDir, 0o755); err == nil {
		_ = watchDirRecursive(fsw, chatsDir)
	}

	go w.loop(fsw, aiDir)
	log.Printf("[watcher] started for %s", aiDir)
}

// Stop closes the underlying fsnotify watcher.
func (w *PipelineWatcher) Stop() {
	w.mu.Lock()
	defer w.mu.Unlock()
	if w.fsw != nil {
		_ = w.fsw.Close()
		w.fsw = nil
	}
}

func (w *PipelineWatcher) loop(fsw *fsnotify.Watcher, aiDir string) {
	type entry struct{ t *time.Timer }
	debounce := make(map[string]*entry)
	var dmu sync.Mutex

	fire := func(path string) {
		dmu.Lock()
		defer dmu.Unlock()
		if e, ok := debounce[path]; ok {
			e.t.Reset(300 * time.Millisecond)
			return
		}
		t := time.AfterFunc(300*time.Millisecond, func() {
			dmu.Lock()
			delete(debounce, path)
			dmu.Unlock()
			w.handleChange(aiDir, path)
		})
		debounce[path] = &entry{t}
	}

	for {
		select {
		case event, ok := <-fsw.Events:
			if !ok {
				return
			}
			if event.Has(fsnotify.Create) {
				if info, err := os.Stat(event.Name); err == nil && info.IsDir() {
					_ = fsw.Add(event.Name)
				}
			}
			if event.Has(fsnotify.Write) || event.Has(fsnotify.Create) {
				fire(event.Name)
			}
		case err, ok := <-fsw.Errors:
			if !ok {
				return
			}
			log.Printf("[watcher] error: %v", err)
		}
	}
}

func (w *PipelineWatcher) handleChange(aiDir, path string) {
	stateFile := stateFilePath(aiDir)
	base := filepath.Base(path)

	switch {
	case path == stateFile:
		w.onStateChange(aiDir)
	case base == "qna.json":
		if w.cb.OnQnaPending != nil {
			w.cb.OnQnaPending(path)
		}
	default:
		if w.cb.OnFileChanged != nil {
			w.cb.OnFileChanged(path)
		}
	}
}

func (w *PipelineWatcher) onStateChange(aiDir string) {
	state, err := readState(aiDir)
	if err != nil || state == nil {
		return
	}

	if w.cb.OnStateChanged != nil {
		w.cb.OnStateChanged(state)
	}

	taskID := state.GetTaskID()
	phase := state.Phase
	agents := state.Agents

	// Report failed agents
	for agent, status := range agents {
		if status == StatusFailed {
			if w.cb.OnAgentFailed != nil {
				w.cb.OnAgentFailed(taskID, phase, agent)
			}
		}
	}

	// Check AND-gates and phase transitions only when no failures
	hasFailures := false
	for _, s := range agents {
		if s == StatusFailed {
			hasFailures = true
			break
		}
	}
	if hasFailures {
		return
	}

	if w.checkAndGates(state, taskID) {
		return
	}
	w.checkPhaseTransition(aiDir, state, taskID)
}

func (w *PipelineWatcher) checkAndGates(state *PipelineState, taskID string) bool {
	phase := state.Phase
	agents := state.Agents

	for _, gate := range andGates {
		if gate.phase != phase {
			continue
		}
		allDone := true
		for _, a := range gate.agents {
			if agents[a] != StatusDone {
				allDone = false
				break
			}
		}
		if !allDone {
			continue
		}

		key := phase + ":" + gate.trigger
		w.mu.Lock()
		fired := w.firedGates[key]
		w.mu.Unlock()
		if fired {
			continue
		}

		targetAgent := gate.trigger
		if idx := strings.LastIndex(gate.trigger, "/"); idx >= 0 {
			targetAgent = gate.trigger[idx+1:]
		}
		if st := agents[targetAgent]; st == StatusInProgress || st == StatusDone {
			w.mu.Lock()
			w.firedGates[key] = true
			w.mu.Unlock()
			continue
		}

		w.mu.Lock()
		w.firedGates[key] = true
		w.mu.Unlock()

		log.Printf("[watcher] AND-gate [%s]: %s → %s", phase, strings.Join(gate.agents, "+"), gate.trigger)
		if w.cb.TriggerAgent != nil {
			go w.cb.TriggerAgent(gate.trigger, taskID)
		}
		return true
	}
	return false
}

func (w *PipelineWatcher) checkPhaseTransition(aiDir string, state *PipelineState, taskID string) {
	phase := state.Phase
	orchestrator := phaseOrchestrators[phase]
	if orchestrator == "" || state.Agents[orchestrator] != StatusDone {
		return
	}

	idx := -1
	for i, p := range phaseOrder {
		if p == phase {
			idx = i
			break
		}
	}
	if idx < 0 {
		return
	}

	if idx < len(phaseOrder)-1 {
		nextPhase := phaseOrder[idx+1]
		log.Printf("[watcher] phase %q → %q", phase, nextPhase)

		_ = advancePhase(aiDir, nextPhase)

		w.mu.Lock()
		for k := range w.firedGates {
			if strings.HasPrefix(k, nextPhase+":") {
				delete(w.firedGates, k)
			}
		}
		w.mu.Unlock()

		if w.cb.OnPhaseAdvanced != nil {
			w.cb.OnPhaseAdvanced(taskID, phase, nextPhase)
		}
		nextOrchestrator := phaseOrchestrators[nextPhase]
		if w.cb.TriggerAgent != nil {
			go w.cb.TriggerAgent(nextPhase+"/"+nextOrchestrator, taskID)
		}
	} else {
		log.Printf("[watcher] pipeline complete (task-id: %s)", taskID)
		if w.cb.OnPipelineComplete != nil {
			w.cb.OnPipelineComplete(taskID)
		}
		if w.cb.TriggerAgent != nil {
			go w.cb.TriggerAgent("office-manager", taskID)
		}
	}
}

func watchDirRecursive(fsw *fsnotify.Watcher, root string) error {
	return filepath.WalkDir(root, func(path string, d os.DirEntry, err error) error {
		if err != nil || !d.IsDir() {
			return nil
		}
		return fsw.Add(path)
	})
}

// advancePhase atomically updates the "phase" field in pipeline-state.json.
func advancePhase(aiDir, nextPhase string) error {
	path := stateFilePath(aiDir)
	mu := fileMutex(path)
	mu.Lock()
	defer mu.Unlock()

	state, err := readState(aiDir)
	if err != nil {
		return err
	}
	state.Phase = nextPhase

	out, _ := json.MarshalIndent(state, "", "  ")
	tmp := path + ".tmp"
	if err := os.WriteFile(tmp, out, 0o644); err != nil {
		return err
	}
	return os.Rename(tmp, path)
}
