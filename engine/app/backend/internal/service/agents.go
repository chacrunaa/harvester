package service

import (
	"fmt"

	scripts "harvester/scripts"
	"harvester/backend/internal/domain"
)

type agentsService struct {
	harvestAiDir string
	projects     *projectsService
	llm          *llmService
}

func NewAgentsService(harvestAiDir string, projects *projectsService, llm *llmService) *agentsService {
	return &agentsService{
		harvestAiDir: harvestAiDir,
		projects:     projects,
		llm:          llm,
	}
}

func (s *agentsService) Trigger(agentID, taskID string) (*domain.AgentRunResult, error) {
	aiDir := s.projects.ActiveAiDir()
	if aiDir == "" {
		return nil, fmt.Errorf("no active project")
	}
	return s.RunAgent(agentID, taskID, aiDir, false)
}

func (s *agentsService) RunAgent(agentID, taskID, aiDir string, dryRun bool) (*domain.AgentRunResult, error) {
	if aiDir == "" {
		aiDir = s.projects.ActiveAiDir()
	}
	if aiDir == "" {
		return nil, fmt.Errorf("no active project")
	}

	result := scripts.RunAgent(agentID, scripts.RunOptions{
		HarvestAiDir: s.harvestAiDir,
		AIDir:        aiDir,
		TaskID:       taskID,
		DryRun:       dryRun,
		LLM:          s.llm.Config(llmCallOptions{}),
	})
	return &domain.AgentRunResult{Status: result.Status, Error: result.Error}, nil
}
