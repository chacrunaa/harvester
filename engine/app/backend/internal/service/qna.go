package service

import (
	"encoding/json"
	"os"
	"path/filepath"

	"harvester/backend/internal/constants"
	"harvester/backend/internal/domain"
	"harvester/backend/internal/repository"
)

type qnaService struct{}

func NewQnaService() *qnaService { return &qnaService{} }

func (s *qnaService) readRaw(path string) ([]domain.QnaQuestion, error) {
	data, err := os.ReadFile(path)
	if err != nil {
		return nil, err
	}
	var arr []domain.QnaQuestion
	if err := json.Unmarshal(data, &arr); err == nil {
		return arr, nil
	}
	var obj struct {
		Questions []domain.QnaQuestion `json:"questions"`
	}
	if err := json.Unmarshal(data, &obj); err != nil {
		return nil, err
	}
	return obj.Questions, nil
}

func (s *qnaService) HasUnanswered(questions []domain.QnaQuestion) bool {
	for _, q := range questions {
		if q.Answer == "" {
			return true
		}
	}
	return false
}

func (s *qnaService) Answer(qnaPath string, answers []domain.QnaAnswer) error {
	questions, err := s.readRaw(qnaPath)
	if err != nil {
		return err
	}
	answerMap := make(map[string]string, len(answers))
	for _, a := range answers {
		answerMap[a.ID] = a.Answer
	}
	for i, q := range questions {
		if ans, ok := answerMap[q.ID]; ok {
			questions[i].Answer = ans
		}
	}
	return repository.WriteJSONAtomic(qnaPath, questions)
}

func (s *qnaService) ScanPending(chatsDir string) ([]domain.PendingQna, error) {
	var pending []domain.PendingQna
	err := filepath.WalkDir(chatsDir, func(path string, d os.DirEntry, err error) error {
		if err != nil || d.IsDir() || d.Name() != constants.FileQna {
			return nil
		}
		questions, rerr := s.readRaw(path)
		if rerr != nil || !s.HasUnanswered(questions) {
			return nil
		}
		rel, _ := filepath.Rel(chatsDir, filepath.Dir(path))
		unanswered := make([]domain.QnaQuestion, 0)
		for _, q := range questions {
			if q.Answer == "" {
				unanswered = append(unanswered, q)
			}
		}
		pending = append(pending, domain.PendingQna{
			AgentID:   rel,
			Questions: unanswered,
		})
		return nil
	})
	return pending, err
}
