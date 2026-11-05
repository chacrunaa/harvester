package lib

import (
	"strings"
	"testing"
)

var sampleResponse = `Вот мой анализ продукта.

<file name="report.md">
# Product Analysis
## Problem
Users forget tasks.
</file>

<file name="qna.json">
{"questions": [{"id": 1, "question": "Целевая аудитория?", "answer": null}]}
</file>
`

func TestParseFiles_TwoBlocks(t *testing.T) {
	got := ParseFiles(sampleResponse)
	if len(got) != 2 {
		t.Fatalf("expected 2 files, got %d", len(got))
	}
	if _, ok := got["report.md"]; !ok {
		t.Error("report.md not found")
	}
	if _, ok := got["qna.json"]; !ok {
		t.Error("qna.json not found")
	}
	if !strings.Contains(got["report.md"], "Product Analysis") {
		t.Error("report.md content mismatch")
	}
}

func TestParseFiles_NoTags(t *testing.T) {
	if len(ParseFiles("нет тегов")) != 0 {
		t.Error("expected 0 files for response without <file> tags")
	}
}

func TestParseFiles_Empty(t *testing.T) {
	if len(ParseFiles("")) != 0 {
		t.Error("expected 0 files for empty string")
	}
}

func TestHasUnansweredQuestions_NullAnswer(t *testing.T) {
	qna := `{"questions": [{"id": 1, "question": "Q?", "answer": null}]}`
	if !HasUnansweredQuestions(qna) {
		t.Error("expected true for null answer")
	}
}

func TestHasUnansweredQuestions_EmptyAnswer(t *testing.T) {
	qna := `{"questions": [{"id": 1, "question": "Q?", "answer": ""}]}`
	if !HasUnansweredQuestions(qna) {
		t.Error("expected true for empty string answer")
	}
}

func TestHasUnansweredQuestions_AllAnswered(t *testing.T) {
	qna := `{"questions": [{"id": 1, "question": "Q?", "answer": "A!"}]}`
	if HasUnansweredQuestions(qna) {
		t.Error("expected false when all questions answered")
	}
}

func TestHasUnansweredQuestions_MixedAnswers(t *testing.T) {
	qna := `{"questions": [
		{"id": 1, "question": "Q1?", "answer": "A1"},
		{"id": 2, "question": "Q2?", "answer": null}
	]}`
	if !HasUnansweredQuestions(qna) {
		t.Error("expected true when at least one question is unanswered")
	}
}

func TestHasUnansweredQuestions_BareArray(t *testing.T) {
	qna := `[{"question": "Q?", "answer": null}]`
	if !HasUnansweredQuestions(qna) {
		t.Error("expected true for bare array format with null answer")
	}
}
