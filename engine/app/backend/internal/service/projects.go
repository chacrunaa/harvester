package service

import (
	"fmt"
	"path/filepath"
	"sync"
	"time"

	"harvester/backend/internal/constants"
	"harvester/backend/internal/domain"
	"harvester/backend/internal/repository"
)

type projectsService struct {
	mu        sync.RWMutex
	activeDir string
	rootDir   string
	stubsDir  string
	onChange  []func(string)
}

func NewProjectsService(rootDir, stubsDir, initialAiDir string) *projectsService {
	return &projectsService{
		rootDir:   rootDir,
		stubsDir:  stubsDir,
		activeDir: initialAiDir,
	}
}

func (s *projectsService) ActiveAiDir() string {
	s.mu.RLock()
	defer s.mu.RUnlock()
	return s.activeDir
}

func (s *projectsService) SwitchTo(aiDir string) {
	s.mu.Lock()
	s.activeDir = aiDir
	cbs := make([]func(string), len(s.onChange))
	copy(cbs, s.onChange)
	s.mu.Unlock()

	for _, cb := range cbs {
		cb(aiDir)
	}
}

func (s *projectsService) OnChange(fn func(string)) {
	s.mu.Lock()
	s.onChange = append(s.onChange, fn)
	s.mu.Unlock()
}

func (s *projectsService) GenerateTaskID() string {
	return fmt.Sprintf(constants.FmtPipelineTaskID, time.Now().UTC().Format(constants.LayoutTaskID))
}

func (s *projectsService) List() ([]domain.ProjectInfo, error) {
	projectsFile := filepath.Join(s.stubsDir, constants.FileProjects)
	entries := repository.ReadJSONOr[[]domain.ProjectListEntry](projectsFile, nil)

	activeDir := s.ActiveAiDir()
	var out []domain.ProjectInfo
	for _, entry := range entries {
		info, err := s.resolveProject(entry)
		if err != nil || info == nil {
			continue
		}
		info.Active = info.AiDir == activeDir
		out = append(out, *info)
	}
	return out, nil
}

func (s *projectsService) resolveProject(entry domain.ProjectListEntry) (*domain.ProjectInfo, error) {
	base := filepath.Join(s.rootDir, entry.Path)

	innerAi := filepath.Join(base, constants.DirAI)
	if repository.Exists(filepath.Join(innerAi, constants.FilePipelineState)) {
		state := repository.ReadJSONOr[*domain.PipelineState](
			filepath.Join(innerAi, constants.FilePipelineState), nil,
		)
		return &domain.ProjectInfo{
			ID:    entry.Path,
			Label: entry.Name,
			AiDir: innerAi,
			State: state,
		}, nil
	}

	if repository.Exists(filepath.Join(base, constants.FilePipelineState)) {
		state := repository.ReadJSONOr[*domain.PipelineState](
			filepath.Join(base, constants.FilePipelineState), nil,
		)
		return &domain.ProjectInfo{
			ID:    entry.Path,
			Label: entry.Name,
			AiDir: base,
			State: state,
		}, nil
	}

	return nil, nil
}
