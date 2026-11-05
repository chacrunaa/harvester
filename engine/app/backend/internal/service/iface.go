package service

import "harvester/backend/internal/domain"

// Subscriber receives broadcast messages from Hub.
type Subscriber interface {
	Receive(data []byte)
}

// Service interfaces used at the transport boundary.

type PipelineSvc interface {
	Read(aiDir string) (*domain.PipelineState, error)
	ResetPhaseAgents(aiDir, phase string) error
	UpdateAgent(aiDir, agentName, status string) error
}

type ProjectsSvc interface {
	ActiveAiDir() string
	SwitchTo(aiDir string)
	List() ([]domain.ProjectInfo, error)
}

type QnaSvc interface {
	ScanPending(chatsDir string) ([]domain.PendingQna, error)
	Answer(qnaPath string, answers []domain.QnaAnswer) error
}

type ChatsSvc interface {
	Get(phase string) ([]domain.ChatMessage, error)
	Append(phase string, msg domain.ChatMessage) (domain.ChatMessage, error)
	ChatWithAgent(phase, agentID, userMessage string, history []domain.ChatMessage) (domain.ChatMessage, error)
}

type AgentsSvc interface {
	Trigger(agentID, taskID string) (*domain.AgentRunResult, error)
}

type TasksSvc interface {
	List() ([]domain.Task, error)
}

type SettingsSvc interface {
	Snapshot() domain.SettingsSnapshot
	Update(provider, apiKey string) (domain.SettingsSnapshot, error)
}

type WatcherSvc interface {
	Start()
}
