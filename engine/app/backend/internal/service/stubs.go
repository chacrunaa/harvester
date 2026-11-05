package service

import (
	"encoding/json"
	"log"
	"os"
	"path/filepath"
	"strings"
)

type stubsService struct {
	stubsDir string
}

func NewStubsService(stubsDir string) *stubsService {
	return &stubsService{stubsDir: stubsDir}
}

// DeriveProjectID derives a project ID from aiDir relative to poligonsDir.
func (s *stubsService) DeriveProjectID(aiDir, poligonsDir string) string {
	rel, err := filepath.Rel(poligonsDir, filepath.Dir(aiDir))
	if err != nil {
		return ""
	}
	return filepath.ToSlash(rel)
}

// ApplyOne fills in stub answers for a qna.json file if stubs exist for the project.
func (s *stubsService) ApplyOne(projectID, aiDir, qnaPath string) {
	stubFile := filepath.Join(s.stubsDir, projectID+".json")
	data, err := os.ReadFile(stubFile)
	if err != nil {
		return
	}

	var stubs map[string]interface{}
	if err := json.Unmarshal(data, &stubs); err != nil {
		return
	}

	// Derive relative path of qna file within chats/
	rel, err := filepath.Rel(filepath.Join(aiDir, "chats"), qnaPath)
	if err != nil {
		return
	}
	agentID := filepath.ToSlash(filepath.Dir(rel))

	stubAnswers, ok := stubs[agentID]
	if !ok {
		// Try with slash-based key matching
		for k, v := range stubs {
			if strings.EqualFold(filepath.ToSlash(k), agentID) {
				stubAnswers = v
				break
			}
		}
	}
	if stubAnswers == nil {
		return
	}

	// Read existing qna, apply stub answers
	qnaData, err := os.ReadFile(qnaPath)
	if err != nil {
		return
	}

	var questions []map[string]interface{}
	if err := json.Unmarshal(qnaData, &questions); err != nil {
		return
	}

	answersMap, ok := stubAnswers.(map[string]interface{})
	if !ok {
		return
	}

	for i, q := range questions {
		id, _ := q["id"].(string)
		if id == "" {
			continue
		}
		if ans, ok := answersMap[id]; ok && q["answer"] == nil {
			questions[i]["answer"] = ans
		}
	}

	result, err := json.MarshalIndent(questions, "", "  ")
	if err != nil {
		return
	}
	if writeErr := os.WriteFile(qnaPath, result, 0o644); writeErr != nil {
		log.Printf("stubs: write error: %v", writeErr)
	}
}
