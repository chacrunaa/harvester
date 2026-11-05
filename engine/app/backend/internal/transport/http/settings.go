package handlers

import (
	"net/http"

	"github.com/gin-gonic/gin"

	"harvester/backend/internal/service"
)

type settingsHandler struct {
	settings service.SettingsSvc
}

func NewSettingsHandler(settings service.SettingsSvc) *settingsHandler {
	return &settingsHandler{settings: settings}
}

func (h *settingsHandler) Get(c *gin.Context) {
	c.JSON(http.StatusOK, h.settings.Snapshot())
}

func (h *settingsHandler) Update(c *gin.Context) {
	var body struct {
		Provider string `json:"provider"`
		ApiKey   string `json:"apiKey"`
	}
	if err := c.ShouldBindJSON(&body); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}
	snap, err := h.settings.Update(body.Provider, body.ApiKey)
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}
	c.JSON(http.StatusOK, snap)
}
