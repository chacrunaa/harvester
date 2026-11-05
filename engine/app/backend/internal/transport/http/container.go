package handlers

import (
	"harvester/backend/internal/service"
)

type Container struct {
	Pipeline *pipelineHandler
	Projects *projectsHandler
	Qna      *qnaHandler
	Chats    *chatsHandler
	Agents   *agentsHandler
	Tasks    *tasksHandler
	Settings *settingsHandler
}

func NewContainer(c *service.Container, templatesDir string) *Container {
	return &Container{
		Pipeline: NewPipelineHandler(c.Pipeline, c.Projects, c.Hub),
		Projects: NewProjectsHandler(c.Projects, c.Pipeline, c.Hub, templatesDir),
		Qna:      NewQnaHandler(c.Qna, c.Projects),
		Chats:    NewChatsHandler(c.Chats, c.Hub),
		Agents:   NewAgentsHandler(c.Agents, c.Pipeline, c.Projects, c.Hub),
		Tasks:    NewTasksHandler(c.Tasks),
		Settings: NewSettingsHandler(c.Settings),
	}
}
