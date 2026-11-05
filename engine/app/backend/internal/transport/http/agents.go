package handlers

import (
	"net/http"

	"github.com/gin-gonic/gin"

	"harvester/backend/internal/service"
)

type agentsHandler struct {
	agents   service.AgentsSvc
	pipeline service.PipelineSvc
	projects service.ProjectsSvc
	hub      *service.Hub
}

func NewAgentsHandler(
	agents service.AgentsSvc,
	pipeline service.PipelineSvc,
	projects service.ProjectsSvc,
	h *service.Hub,
) *agentsHandler {
	return &agentsHandler{agents: agents, pipeline: pipeline, projects: projects, hub: h}
}

func (h *agentsHandler) Trigger(c *gin.Context) {
	agentID := c.Param("agentId")
	var body struct {
		TaskID string `json:"taskId"`
	}
	if err := c.ShouldBindJSON(&body); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}

	result, err := h.agents.Trigger(agentID, body.TaskID)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}
	c.JSON(http.StatusOK, result)
}
