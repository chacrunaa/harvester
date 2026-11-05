package handlers

import (
	"fmt"
	"net/http"
	"os"
	"path/filepath"
	"time"

	"github.com/gin-gonic/gin"

	"harvester/backend/internal/constants"
	"harvester/backend/internal/repository"
	"harvester/backend/internal/service"
)

type projectsHandler struct {
	projects     service.ProjectsSvc
	pipeline     service.PipelineSvc
	hub          *service.Hub
	templatesDir string
}

func NewProjectsHandler(
	projects service.ProjectsSvc,
	pipeline service.PipelineSvc,
	h *service.Hub,
	templatesDir string,
) *projectsHandler {
	return &projectsHandler{
		projects:     projects,
		pipeline:     pipeline,
		hub:          h,
		templatesDir: templatesDir,
	}
}

func (h *projectsHandler) List(c *gin.Context) {
	list, err := h.projects.List()
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}
	c.JSON(http.StatusOK, list)
}

func (h *projectsHandler) Open(c *gin.Context) {
	var body struct {
		AiDir string `json:"aiDir"`
	}
	if err := c.ShouldBindJSON(&body); err != nil || body.AiDir == "" {
		c.JSON(http.StatusBadRequest, gin.H{"error": "aiDir required"})
		return
	}
	if !repository.Exists(filepath.Join(body.AiDir, constants.FilePipelineState)) {
		c.JSON(http.StatusNotFound, gin.H{"error": "pipeline-state.json not found in given aiDir"})
		return
	}
	h.projects.SwitchTo(body.AiDir)
	state, _ := h.pipeline.Read(body.AiDir)
	h.hub.Broadcast("project:opened", gin.H{"aiDir": body.AiDir, "state": state})
	c.JSON(http.StatusOK, gin.H{"ok": true, "aiDir": body.AiDir, "state": state})
}

func (h *projectsHandler) Create(c *gin.Context) {
	var body struct {
		ProjectName string `json:"projectName"`
		Description string `json:"description"`
		Path        string `json:"path"`
	}
	if err := c.ShouldBindJSON(&body); err != nil || body.Path == "" {
		c.JSON(http.StatusBadRequest, gin.H{"error": "path required"})
		return
	}

	aiDir := filepath.Join(body.Path, constants.DirAI)
	taskID := fmt.Sprintf(constants.FmtPipelineTaskID, time.Now().UTC().Format(constants.LayoutTaskID))
	createdAt := time.Now().UTC().Format(time.RFC3339)

	templAi := filepath.Join(h.templatesDir, "ai")
	if repository.Exists(templAi) {
		_ = copyDirRecursive(templAi, aiDir)
	}

	_ = repository.WriteJSONAtomic(filepath.Join(aiDir, constants.FilePipelineState), map[string]interface{}{
		"task-id":    taskID,
		"created_at": createdAt,
		"phase":      "init",
		"agents":     map[string]string{"office-manager": constants.StatusWaiting},
	})

	h.projects.SwitchTo(aiDir)
	h.hub.Broadcast("project:opened", gin.H{"aiDir": aiDir})
	c.JSON(http.StatusCreated, gin.H{"ok": true, "aiDir": aiDir, "taskId": taskID})
}

func copyDirRecursive(src, dst string) error {
	_ = os.MkdirAll(dst, 0o755)
	entries, err := os.ReadDir(src)
	if err != nil {
		return err
	}
	for _, e := range entries {
		s := filepath.Join(src, e.Name())
		d := filepath.Join(dst, e.Name())
		if e.IsDir() {
			_ = copyDirRecursive(s, d)
		} else {
			_ = os.MkdirAll(filepath.Dir(d), 0o755)
			data, rerr := os.ReadFile(s)
			if rerr == nil {
				_ = os.WriteFile(d, data, 0o644)
			}
		}
	}
	return nil
}
