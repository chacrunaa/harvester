package handlers

import (
	"net/http"
	"path/filepath"

	"github.com/gin-gonic/gin"

	"harvester/backend/internal/constants"
	"harvester/backend/internal/domain"
	"harvester/backend/internal/service"
)

type qnaHandler struct {
	qna      service.QnaSvc
	projects service.ProjectsSvc
}

func NewQnaHandler(qna service.QnaSvc, projects service.ProjectsSvc) *qnaHandler {
	return &qnaHandler{qna: qna, projects: projects}
}

func (h *qnaHandler) ListPending(c *gin.Context) {
	aiDir := h.projects.ActiveAiDir()
	if aiDir == "" {
		c.JSON(http.StatusOK, []interface{}{})
		return
	}
	chatsDir := filepath.Join(aiDir, constants.DirChats)
	pending, err := h.qna.ScanPending(chatsDir)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}
	if pending == nil {
		pending = []domain.PendingQna{}
	}
	c.JSON(http.StatusOK, pending)
}

func (h *qnaHandler) Answer(c *gin.Context) {
	agentID := c.Param("agentId")
	var body struct {
		TaskID  string             `json:"taskId"`
		Answers []domain.QnaAnswer `json:"answers"`
	}
	if err := c.ShouldBindJSON(&body); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}

	aiDir := h.projects.ActiveAiDir()
	if aiDir == "" {
		c.JSON(http.StatusBadRequest, gin.H{"error": "no active project"})
		return
	}

	qnaPath := filepath.Join(aiDir, constants.DirChats, filepath.FromSlash(agentID), constants.FileQna)
	if err := h.qna.Answer(qnaPath, body.Answers); err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}
	c.JSON(http.StatusOK, gin.H{"ok": true})
}
