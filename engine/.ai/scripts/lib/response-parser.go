package lib

import (
	"encoding/json"
	"regexp"
	"strings"
)

var fileBlockRe = regexp.MustCompile(`<file\s+name="([^"]+)">([\s\S]*?)</file>`)

// ParseFiles extracts <file name="...">content</file> blocks from an LLM response.
func ParseFiles(text string) map[string]string {
	files := make(map[string]string)
	for _, m := range fileBlockRe.FindAllStringSubmatch(text, -1) {
		name := strings.TrimSpace(m[1])
		content := strings.TrimPrefix(m[2], "\n")
		content = strings.TrimSuffix(content, "\n")
		files[name] = content
	}
	return files
}

// HasUnansweredQuestions returns true if any question in a qna JSON blob
// has a null or empty answer. Handles {"questions":[...]} and bare array formats.
func HasUnansweredQuestions(qnaContent string) bool {
	type q struct {
		Answer *string `json:"answer"`
	}
	check := func(questions []q) bool {
		for _, item := range questions {
			if item.Answer == nil || *item.Answer == "" {
				return true
			}
		}
		return false
	}
	var obj struct {
		Questions []q `json:"questions"`
	}
	if err := json.Unmarshal([]byte(qnaContent), &obj); err == nil {
		return check(obj.Questions)
	}
	var arr []q
	if err := json.Unmarshal([]byte(qnaContent), &arr); err == nil {
		return check(arr)
	}
	return false
}
