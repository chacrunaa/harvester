package handlers

import (
	"net/http"
	"os"
	"path/filepath"

	"github.com/gin-gonic/gin"

	"harvester/backend/internal/constants"
	"harvester/backend/internal/service"
)

type pipelineHandler struct {
	pipeline service.PipelineSvc
	projects service.ProjectsSvc
	hub      *service.Hub
}

func NewPipelineHandler(pipeline service.PipelineSvc, projects service.ProjectsSvc, h *service.Hub) *pipelineHandler {
	return &pipelineHandler{pipeline: pipeline, projects: projects, hub: h}
}

func (h *pipelineHandler) GetState(c *gin.Context) {
	aiDir := h.projects.ActiveAiDir()
	if aiDir == "" {
		c.JSON(http.StatusNotFound, gin.H{"error": "no active project"})
		return
	}
	state, err := h.pipeline.Read(aiDir)
	if err != nil {
		c.JSON(http.StatusNotFound, gin.H{"error": "pipeline-state.json not found"})
		return
	}
	c.JSON(http.StatusOK, state)
}

func (h *pipelineHandler) PhaseOk(c *gin.Context) {
	phase := c.Param("phase")
	var body struct {
		TaskID string `json:"taskId"`
	}
	_ = c.ShouldBindJSON(&body)
	h.hub.Broadcast("pipeline:ok", gin.H{"taskId": body.TaskID, "phase": phase})
	c.JSON(http.StatusOK, gin.H{"ok": true})
}

func (h *pipelineHandler) PhaseNotOk(c *gin.Context) {
	phase := c.Param("phase")
	var body struct {
		TaskID   string `json:"taskId"`
		Feedback string `json:"feedback"`
	}
	_ = c.ShouldBindJSON(&body)

	aiDir := h.projects.ActiveAiDir()
	if aiDir != "" && body.Feedback != "" {
		feedbackFile := filepath.Join(aiDir, constants.DirChats, phase, "feedback.md")
		_ = os.MkdirAll(filepath.Dir(feedbackFile), 0o755)
		content := "# Фидбэк пользователя\n\n**task-id:** " + body.TaskID + "\n**фаза:** " + phase + "\n\n" + body.Feedback + "\n"
		_ = os.WriteFile(feedbackFile, []byte(content), 0o644)
		_ = h.pipeline.ResetPhaseAgents(aiDir, phase)
	}

	h.hub.Broadcast("pipeline:notok", gin.H{"taskId": body.TaskID, "phase": phase, "feedback": body.Feedback})
	c.JSON(http.StatusOK, gin.H{"ok": true})
}

func (h *pipelineHandler) AgentRetry(c *gin.Context) {
	agent := c.Param("agentName")
	var body struct {
		TaskID string `json:"taskId"`
	}
	_ = c.ShouldBindJSON(&body)
	h.hub.Broadcast("agent:retry", gin.H{"taskId": body.TaskID, "agent": agent})
	c.JSON(http.StatusOK, gin.H{"ok": true})
}

func (h *pipelineHandler) AgentSkip(c *gin.Context) {
	agent := c.Param("agentName")
	var body struct {
		TaskID string `json:"taskId"`
	}
	_ = c.ShouldBindJSON(&body)

	aiDir := h.projects.ActiveAiDir()
	if aiDir != "" {
		_ = h.pipeline.UpdateAgent(aiDir, agent, constants.StatusDone)
	}
	h.hub.Broadcast("agent:skip", gin.H{"taskId": body.TaskID, "agent": agent})
	c.JSON(http.StatusOK, gin.H{"ok": true})
}
