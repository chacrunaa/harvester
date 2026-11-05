package service

import (
	"harvester/backend/internal/config"
	"harvester/backend/internal/constants"
)

type Container struct {
	Pipeline *pipelineService
	Projects *projectsService
	Qna      *qnaService
	Tasks    *tasksService
	Settings *settingsService
	Llm      *llmService
	Chats    *chatsService
	Agents   *agentsService
	Stubs    *stubsService
	Watcher  *watcherService
	Hub      *Hub
}

func NewContainer(cfg *config.Config) *Container {
	h := NewHub()

	projectsSvc := NewProjectsService(cfg.Paths.RootDir, cfg.Paths.StubsDir, cfg.Paths.AiDir)
	pipelineSvc := NewPipelineService()
	qnaSvc := NewQnaService()
	tasksSvc := NewTasksService(projectsSvc)
	settingsSvc := NewSettingsService(cfg.LLM.Provider, map[constants.Provider]string{
		constants.ProviderClaude:   cfg.LLM.Models.Anthropic,
		constants.ProviderCodex:    cfg.LLM.Models.OpenAI,
		constants.ProviderDeepSeek: cfg.LLM.Models.DeepSeek,
		constants.ProviderGemini:   cfg.LLM.Models.Gemini,
	})
	llmSvc := NewLlmService(settingsSvc)
	chatsSvc := NewChatsService(projectsSvc, llmSvc, cfg.Paths.AgentsDir)
	agentsSvc := NewAgentsService(cfg.Paths.HarvestAiDir, projectsSvc, llmSvc)
	stubsSvc := NewStubsService(cfg.Paths.StubsDir)
	watcherSvc := NewWatcherService(pipelineSvc, projectsSvc, qnaSvc, agentsSvc, stubsSvc, h, cfg.Paths.PoligonsDir)

	return &Container{
		Pipeline: pipelineSvc,
		Projects: projectsSvc,
		Qna:      qnaSvc,
		Tasks:    tasksSvc,
		Settings: settingsSvc,
		Llm:      llmSvc,
		Chats:    chatsSvc,
		Agents:   agentsSvc,
		Stubs:    stubsSvc,
		Watcher:  watcherSvc,
		Hub:      h,
	}
}
