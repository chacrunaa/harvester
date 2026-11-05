package domain

import "harvester/backend/internal/constants"

type PipelineState struct {
	TaskID       string                           `json:"task-id,omitempty"`
	TaskIDLegacy string                           `json:"task_id,omitempty"`
	Phase        string                           `json:"phase,omitempty"`
	Agents       map[string]constants.AgentStatus `json:"agents"`
	NextTrigger  interface{}                      `json:"next-trigger,omitempty"`
	CreatedAt    string                           `json:"created_at,omitempty"`
}

func (s *PipelineState) GetTaskID() string {
	if s.TaskID != "" {
		return s.TaskID
	}
	return s.TaskIDLegacy
}
