package service

import (
	"fmt"
	"path/filepath"
	"time"

	"harvester/backend/internal/constants"
	"harvester/backend/internal/domain"
	"harvester/backend/internal/repository"
)

type tasksService struct {
	projects *projectsService
}

func NewTasksService(projects *projectsService) *tasksService {
	return &tasksService{projects: projects}
}

func (s *tasksService) tasksFile(aiDir string) string {
	return filepath.Join(aiDir, constants.DirBacklog, constants.FileTasks)
}

func (s *tasksService) List() ([]domain.Task, error) {
	aiDir := s.projects.ActiveAiDir()
	if aiDir == "" {
		return []domain.Task{}, nil
	}
	f := repository.ReadJSONOr[domain.TasksFile](s.tasksFile(aiDir), domain.TasksFile{})
	if f.Tasks == nil {
		return []domain.Task{}, nil
	}
	return f.Tasks, nil
}

func (s *tasksService) Create(title, description string) (domain.Task, error) {
	aiDir := s.projects.ActiveAiDir()
	if aiDir == "" {
		return domain.Task{}, fmt.Errorf("no active project")
	}
	task := domain.Task{
		ID:          fmt.Sprintf(constants.FmtTaskID, time.Now().UnixMilli()),
		Title:       title,
		Description: description,
		Status:      constants.TaskStatusOpen,
		CreatedAt:   time.Now().UTC().Format(time.RFC3339),
	}
	_, err := repository.MutateJSON[domain.TasksFile](s.tasksFile(aiDir), func(cur *domain.TasksFile) *domain.TasksFile {
		if cur == nil {
			cur = &domain.TasksFile{}
		}
		cur.Tasks = append(cur.Tasks, task)
		return cur
	})
	return task, err
}
