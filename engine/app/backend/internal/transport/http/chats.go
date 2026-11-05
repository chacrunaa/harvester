package handlers

import (
	"net/http"

	"github.com/gin-gonic/gin"

	"harvester/backend/internal/domain"
	"harvester/backend/internal/service"
)

type chatsHandler struct {
	chats service.ChatsSvc
	hub   *service.Hub
}

func NewChatsHandler(chats service.ChatsSvc, h *service.Hub) *chatsHandler {
	return &chatsHandler{chats: chats, hub: h}
}

func (h *chatsHandler) Get(c *gin.Context) {
	phase := c.Param("phase")
	msgs, err := h.chats.Get(phase)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}
	c.JSON(http.StatusOK, msgs)
}

func (h *chatsHandler) Post(c *gin.Context) {
	phase := c.Param("phase")
	var body domain.ChatMessage
	if err := c.ShouldBindJSON(&body); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}

	saved, err := h.chats.Append(phase, body)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}

	if len(body.Mentions) > 0 {
		for _, agentID := range body.Mentions {
			history, _ := h.chats.Get(phase)
			agentReply, llmErr := h.chats.ChatWithAgent(phase, agentID, body.Content, history)
			if llmErr != nil {
				continue
			}
			_, _ = h.chats.Append(phase, agentReply)
			h.hub.Broadcast("agent:message", map[string]interface{}{
				"phase":   phase,
				"message": agentReply,
			})
		}
	}

	c.JSON(http.StatusCreated, saved)
}
