package service

import (
	"path/filepath"

	"harvester/backend/internal/constants"
	"harvester/backend/internal/domain"
	"harvester/backend/internal/repository"
)

type pipelineService struct{}

func NewPipelineService() *pipelineService { return &pipelineService{} }

func (s *pipelineService) stateFile(aiDir string) string {
	return filepath.Join(aiDir, constants.FilePipelineState)
}

func (s *pipelineService) Read(aiDir string) (*domain.PipelineState, error) {
	st, err := repository.ReadJSON[domain.PipelineState](s.stateFile(aiDir))
	if err != nil {
		return nil, err
	}
	return &st, nil
}

func (s *pipelineService) WriteAtomic(aiDir string, state *domain.PipelineState) error {
	return repository.WriteJSONAtomic(s.stateFile(aiDir), state)
}

func (s *pipelineService) Mutate(aiDir string, fn func(*domain.PipelineState) *domain.PipelineState) (*domain.PipelineState, error) {
	return repository.MutateJSON[domain.PipelineState](s.stateFile(aiDir), fn)
}

func (s *pipelineService) UpdateAgent(aiDir, agentName, status string) error {
	_, err := s.Mutate(aiDir, func(cur *domain.PipelineState) *domain.PipelineState {
		if cur == nil {
			cur = &domain.PipelineState{Agents: map[string]constants.AgentStatus{}}
		}
		if cur.Agents == nil {
			cur.Agents = map[string]constants.AgentStatus{}
		}
		cur.Agents[agentName] = status
		return cur
	})
	return err
}

func (s *pipelineService) ResetPhaseAgents(aiDir, phase string) error {
	agents := constants.PhaseAgents[phase]
	if len(agents) == 0 {
		return nil
	}
	_, err := s.Mutate(aiDir, func(cur *domain.PipelineState) *domain.PipelineState {
		if cur == nil {
			return cur
		}
		for _, a := range agents {
			if _, ok := cur.Agents[a]; ok {
				cur.Agents[a] = constants.StatusWaiting
			}
		}
		return cur
	})
	return err
}
