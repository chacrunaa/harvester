package service

import (
	"log"
	"os"
	"path/filepath"
	"strings"
	"sync"
	"time"

	"harvester/backend/internal/constants"

	scripts "harvester/scripts"
)

type watcherService struct {
	mu          sync.Mutex
	watcher     *scripts.PipelineWatcher
	inFlight    map[string]bool
	pipeline    *pipelineService
	projects    *projectsService
	qna         *qnaService
	agents      *agentsService
	stubs       *stubsService
	hub         *Hub
	poligonsDir string
}

func NewWatcherService(
	pipeline *pipelineService,
	projects *projectsService,
	qna *qnaService,
	agents *agentsService,
	stubs *stubsService,
	h *Hub,
	poligonsDir string,
) *watcherService {
	return &watcherService{
		pipeline:    pipeline,
		projects:    projects,
		qna:         qna,
		agents:      agents,
		stubs:       stubs,
		hub:         h,
		poligonsDir: poligonsDir,
		inFlight:    make(map[string]bool),
	}
}

func (w *watcherService) Start() {
	w.projects.OnChange(func(aiDir string) {
		w.restart(aiDir)
	})
	if dir := w.projects.ActiveAiDir(); dir != "" {
		w.restart(dir)
	}
}

func (w *watcherService) restart(aiDir string) {
	pw := scripts.NewWatcher(aiDir, w.callbacks(aiDir))
	w.mu.Lock()
	old := w.watcher
	w.watcher = pw
	w.inFlight = make(map[string]bool)
	w.mu.Unlock()
	if old != nil {
		old.Stop()
	}
	if aiDir != "" {
		pw.Start()
	}
}

func (w *watcherService) callbacks(aiDir string) scripts.WatcherCallbacks {
	return scripts.WatcherCallbacks{
		OnStateChanged: func(state *scripts.PipelineState) {
			w.hub.Broadcast(constants.EventPipelineStateChanged, state)
		},
		OnAgentFailed: func(taskID, phase, agent string) {
			w.appendIncident(aiDir, taskID, phase, agent)
			w.hub.Broadcast(constants.EventIncidentNew, map[string]string{
				"taskId": taskID, "phase": phase, "agent": agent,
			})
		},
		OnPhaseAdvanced: func(taskID, from, to string) {
			w.hub.Broadcast(constants.EventPipelinePhaseDone, map[string]string{
				"taskId": taskID, "completedPhase": from, "nextPhase": to,
			})
		},
		OnPipelineComplete: func(taskID string) {
			w.hub.Broadcast(constants.EventPipelineCompleted, map[string]string{"taskId": taskID})
		},
		TriggerAgent: func(agentID, taskID string) {
			w.triggerAgent(agentID, taskID)
		},
		OnQnaPending: func(qnaPath string) {
			w.onQnaFile(aiDir, qnaPath)
		},
		OnFileChanged: func(path string) {
			base := filepath.Base(path)
			if strings.HasSuffix(base, constants.ExtMarkdown) && strings.Contains(base, constants.KeyBrief) {
				w.onBriefFile(aiDir, path)
			}
		},
	}
}

func (w *watcherService) triggerAgent(agentID, taskID string) {
	w.mu.Lock()
	if w.inFlight[agentID] {
		w.mu.Unlock()
		return
	}
	w.inFlight[agentID] = true
	w.mu.Unlock()

	defer func() {
		w.mu.Lock()
		delete(w.inFlight, agentID)
		w.mu.Unlock()
	}()

	log.Printf("watcher: trigger %s", agentID)
	result, err := w.agents.Trigger(agentID, taskID)
	if err != nil {
		log.Printf("watcher: trigger error %s: %v", agentID, err)
		return
	}
	if result != nil && result.Status == "qna-pending" {
		w.hub.Broadcast(constants.EventAgentQnaWaiting, map[string]string{
			"agentId": agentID, "taskId": taskID,
		})
	}
}

func (w *watcherService) onQnaFile(aiDir, path string) {
	projectID := w.stubs.DeriveProjectID(aiDir, w.poligonsDir)
	w.stubs.ApplyOne(projectID, aiDir, path)

	chatsDir := filepath.Join(aiDir, constants.DirChats)
	pending, err := w.qna.ScanPending(chatsDir)
	if err != nil {
		return
	}
	for _, p := range pending {
		w.hub.Broadcast(constants.EventAgentQnaWaiting, map[string]string{
			"agentId": p.AgentID, "taskId": p.TaskID,
		})
	}
}

func (w *watcherService) onBriefFile(aiDir, path string) {
	data, err := os.ReadFile(path)
	if err != nil {
		return
	}
	state, _ := w.pipeline.Read(aiDir)
	var taskID, phase string
	if state != nil {
		taskID = state.GetTaskID()
		phase = state.Phase
	}
	w.hub.Broadcast(constants.EventBriefReady, map[string]string{
		"taskId": taskID, "phase": phase, "content": string(data),
	})
}

func (w *watcherService) appendIncident(aiDir, taskID, phase, agent string) {
	incFile := filepath.Join(aiDir, constants.DirChats, constants.DirOfficeManager, constants.FileIncidents)
	_ = os.MkdirAll(filepath.Dir(incFile), 0o755)
	line := "\n## Инцидент " + time.Now().UTC().Format(time.RFC3339) +
		"\n- task-id: " + taskID +
		"\n- фаза: " + phase +
		"\n- агент: " + agent + "\n"
	f, err := os.OpenFile(incFile, os.O_APPEND|os.O_CREATE|os.O_WRONLY, 0o644)
	if err != nil {
		return
	}
	defer f.Close()
	_, _ = f.WriteString(line)
}
