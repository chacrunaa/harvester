package service

import (
	"fmt"
	"path/filepath"
	"time"

	"harvester/backend/internal/constants"
	"harvester/backend/internal/domain"
	"harvester/backend/internal/repository"
)

type chatsService struct {
	projects  *projectsService
	llm       *llmService
	agentsDir string
}

func NewChatsService(projects *projectsService, llm *llmService, agentsDir string) *chatsService {
	return &chatsService{projects: projects, llm: llm, agentsDir: agentsDir}
}

func (s *chatsService) chatFile(aiDir, phase string) string {
	return filepath.Join(aiDir, constants.DirChats, phase, constants.FileChat)
}

func (s *chatsService) Get(phase string) ([]domain.ChatMessage, error) {
	aiDir := s.projects.ActiveAiDir()
	if aiDir == "" {
		return nil, nil
	}
	msgs := repository.ReadJSONOr[[]domain.ChatMessage](s.chatFile(aiDir, phase), nil)
	if msgs == nil {
		return []domain.ChatMessage{}, nil
	}
	return msgs, nil
}

func (s *chatsService) Append(phase string, msg domain.ChatMessage) (domain.ChatMessage, error) {
	aiDir := s.projects.ActiveAiDir()
	if aiDir == "" {
		return msg, fmt.Errorf("no active project")
	}
	if msg.ID == "" {
		msg.ID = fmt.Sprintf(constants.FmtMessageID, time.Now().UnixMilli())
	}
	if msg.Timestamp == "" {
		msg.Timestamp = time.Now().UTC().Format(time.RFC3339)
	}

	chatPath := s.chatFile(aiDir, phase)
	existing := repository.ReadJSONOr[[]domain.ChatMessage](chatPath, nil)
	existing = append(existing, msg)
	return msg, repository.WriteJSONAtomic(chatPath, existing)
}

func (s *chatsService) ChatWithAgent(phase, agentID, userMessage string, history []domain.ChatMessage) (domain.ChatMessage, error) {
	agentName := agentID
	system := fmt.Sprintf(constants.PromptAgentSystem, agentName)

	reply, err := s.llm.Generate(system, userMessage)
	if err != nil {
		return domain.ChatMessage{}, err
	}
	return domain.ChatMessage{
		Type:      constants.ChatRoleAgent,
		Role:      constants.ChatRoleAgent,
		Agent:     agentName,
		Content:   reply,
		Timestamp: time.Now().UTC().Format(time.RFC3339),
	}, nil
}
