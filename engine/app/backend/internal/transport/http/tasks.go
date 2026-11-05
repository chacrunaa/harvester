package handlers

import (
	"net/http"

	"github.com/gin-gonic/gin"

	"harvester/backend/internal/service"
)

type tasksHandler struct {
	tasks service.TasksSvc
}

func NewTasksHandler(tasks service.TasksSvc) *tasksHandler {
	return &tasksHandler{tasks: tasks}
}

func (h *tasksHandler) List(c *gin.Context) {
	tasks, err := h.tasks.List()
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}
	c.JSON(http.StatusOK, tasks)
}
