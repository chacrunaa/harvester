package lib

import (
	"bytes"
	"encoding/json"
	"fmt"
	"io"
	"log"
	"net/http"
	"os"
	"path/filepath"
	"strings"
	"time"
)

const (
	DefaultMaxTokens = 8192
	DefaultRetries   = 3
	DefaultBaseDelay = 2 * time.Second

	ProviderClaude   = "claude"
	ProviderCodex    = "codex"
	ProviderDeepSeek = "deepseek"
	ProviderGemini   = "gemini"
)

// Config holds everything needed to call an LLM provider.
type Config struct {
	Provider  string
	APIKey    string
	Model     string
	MaxTokens int
	Retries   int
	BaseDelay time.Duration
}

// CallOpts are per-call metadata used for logging.
type CallOpts struct {
	TaskID string
	Agent  string
	LogDir string
}

// Call sends system + user prompts to the configured provider and returns the text response.
func Call(cfg Config, system, user string, opts CallOpts) (string, error) {
	if cfg.MaxTokens == 0 {
		cfg.MaxTokens = DefaultMaxTokens
	}
	if cfg.Retries == 0 {
		cfg.Retries = DefaultRetries
	}
	if cfg.BaseDelay == 0 {
		cfg.BaseDelay = DefaultBaseDelay
	}
	if opts.Agent == "" {
		opts.Agent = "unknown"
	}

	startedAt := time.Now()
	text, inTok, outTok, callErr := dispatchLLM(cfg, system, user)
	duration := time.Since(startedAt)

	if opts.LogDir != "" {
		writeLLMLog(opts.LogDir, llmLogEntry{
			Provider:     cfg.Provider,
			TaskID:       opts.TaskID,
			Agent:        opts.Agent,
			Model:        cfg.Model,
			StartedAt:    startedAt.UTC().Format(time.RFC3339),
			DurationMs:   duration.Milliseconds(),
			InputTokens:  inTok,
			OutputTokens: outTok,
			Status:       llmStatus(callErr),
			Error:        llmErrStr(callErr),
		})
	}

	if callErr != nil {
		return "", callErr
	}
	log.Printf("[llm:%s] %s → %dms | in:%d out:%d",
		cfg.Provider, opts.Agent, duration.Milliseconds(), inTok, outTok)
	return text, nil
}

func dispatchLLM(cfg Config, system, user string) (string, int, int, error) {
	switch cfg.Provider {
	case ProviderCodex:
		return retryLLM(cfg, func() (string, int, int, error) {
			return callOpenAICompat(cfg.APIKey, cfg.Model, cfg.MaxTokens,
				"https://api.openai.com/v1/chat/completions", system, user)
		})
	case ProviderDeepSeek:
		return retryLLM(cfg, func() (string, int, int, error) {
			return callOpenAICompat(cfg.APIKey, cfg.Model, cfg.MaxTokens,
				"https://api.deepseek.com/chat/completions", system, user)
		})
	case ProviderGemini:
		return retryLLM(cfg, func() (string, int, int, error) {
			return callGemini(cfg.APIKey, cfg.Model, cfg.MaxTokens, system, user)
		})
	default: // claude + fallback
		return retryLLM(cfg, func() (string, int, int, error) {
			return callAnthropic(cfg.APIKey, cfg.Model, cfg.MaxTokens, system, user)
		})
	}
}

// ---------------------------------------------------------------------------
// Retry
// ---------------------------------------------------------------------------

type retryableErr struct{ cause error }

func (e *retryableErr) Error() string { return e.cause.Error() }

func retryLLM(cfg Config, fn func() (string, int, int, error)) (string, int, int, error) {
	for i := 0; i < cfg.Retries; i++ {
		text, in, out, err := fn()
		if err == nil {
			return text, in, out, nil
		}
		if _, ok := err.(*retryableErr); !ok {
			return "", 0, 0, err
		}
		if i < cfg.Retries-1 {
			delay := cfg.BaseDelay * (1 << uint(i))
			log.Printf("[llm] attempt %d failed (%v), retry in %v", i+1, err, delay)
			time.Sleep(delay)
		} else {
			return "", 0, 0, err
		}
	}
	return "", 0, 0, fmt.Errorf("all retries exhausted")
}

// ---------------------------------------------------------------------------
// Anthropic
// ---------------------------------------------------------------------------

func callAnthropic(apiKey, model string, maxTokens int, system, user string) (string, int, int, error) {
	if apiKey == "" {
		return "", 0, 0, fmt.Errorf("ANTHROPIC_API_KEY not set")
	}
	body, _ := json.Marshal(map[string]interface{}{
		"model": model, "max_tokens": maxTokens, "system": system,
		"messages": []map[string]string{{"role": "user", "content": user}},
	})
	req, _ := http.NewRequest("POST", "https://api.anthropic.com/v1/messages", bytes.NewReader(body))
	req.Header.Set("x-api-key", apiKey)
	req.Header.Set("anthropic-version", "2023-06-01")
	req.Header.Set("content-type", "application/json")

	resp, err := http.DefaultClient.Do(req)
	if err != nil {
		return "", 0, 0, &retryableErr{fmt.Errorf("anthropic: %w", err)}
	}
	defer resp.Body.Close()
	if resp.StatusCode == 429 || resp.StatusCode >= 500 {
		b, _ := io.ReadAll(resp.Body)
		return "", 0, 0, &retryableErr{fmt.Errorf("anthropic HTTP %d: %s", resp.StatusCode, b)}
	}
	var result struct {
		Content []struct{ Text string `json:"text"` } `json:"content"`
		Usage   *struct {
			InputTokens  int `json:"input_tokens"`
			OutputTokens int `json:"output_tokens"`
		} `json:"usage"`
		Error *struct{ Message string `json:"message"` } `json:"error"`
	}
	if err := json.NewDecoder(resp.Body).Decode(&result); err != nil {
		return "", 0, 0, fmt.Errorf("anthropic parse: %w", err)
	}
	if result.Error != nil {
		return "", 0, 0, fmt.Errorf("anthropic: %s", result.Error.Message)
	}
	if len(result.Content) == 0 {
		return "", 0, 0, fmt.Errorf("anthropic: empty response")
	}
	var in, out int
	if result.Usage != nil {
		in, out = result.Usage.InputTokens, result.Usage.OutputTokens
	}
	return result.Content[0].Text, in, out, nil
}

// ---------------------------------------------------------------------------
// OpenAI-compatible (OpenAI + DeepSeek)
// ---------------------------------------------------------------------------

func callOpenAICompat(apiKey, model string, maxTokens int, endpoint, system, user string) (string, int, int, error) {
	if apiKey == "" {
		return "", 0, 0, fmt.Errorf("API key not set for %s", endpoint)
	}
	body, _ := json.Marshal(map[string]interface{}{
		"model": model, "max_tokens": maxTokens,
		"messages": []map[string]string{
			{"role": "system", "content": system},
			{"role": "user", "content": user},
		},
	})
	req, _ := http.NewRequest("POST", endpoint, bytes.NewReader(body))
	req.Header.Set("Authorization", "Bearer "+apiKey)
	req.Header.Set("Content-Type", "application/json")

	resp, err := http.DefaultClient.Do(req)
	if err != nil {
		return "", 0, 0, &retryableErr{fmt.Errorf("openai: %w", err)}
	}
	defer resp.Body.Close()
	if resp.StatusCode == 429 || resp.StatusCode >= 500 {
		b, _ := io.ReadAll(resp.Body)
		return "", 0, 0, &retryableErr{fmt.Errorf("openai HTTP %d: %s", resp.StatusCode, b)}
	}
	var result struct {
		Choices []struct {
			Message struct{ Content string `json:"content"` } `json:"message"`
		} `json:"choices"`
		Usage *struct {
			PromptTokens     int `json:"prompt_tokens"`
			CompletionTokens int `json:"completion_tokens"`
		} `json:"usage"`
		Error *struct{ Message string `json:"message"` } `json:"error"`
	}
	if err := json.NewDecoder(resp.Body).Decode(&result); err != nil {
		return "", 0, 0, fmt.Errorf("openai parse: %w", err)
	}
	if result.Error != nil {
		return "", 0, 0, fmt.Errorf("openai: %s", result.Error.Message)
	}
	if len(result.Choices) == 0 {
		return "", 0, 0, fmt.Errorf("openai: empty response")
	}
	var in, out int
	if result.Usage != nil {
		in, out = result.Usage.PromptTokens, result.Usage.CompletionTokens
	}
	return result.Choices[0].Message.Content, in, out, nil
}

// ---------------------------------------------------------------------------
// Gemini
// ---------------------------------------------------------------------------

func callGemini(apiKey, model string, maxTokens int, system, user string) (string, int, int, error) {
	if apiKey == "" {
		return "", 0, 0, fmt.Errorf("GEMINI_API_KEY not set")
	}
	type part struct {
		Text string `json:"text"`
	}
	type content struct {
		Parts []part `json:"parts"`
	}
	reqBody := map[string]interface{}{
		"contents":         []content{{Parts: []part{{Text: user}}}},
		"generationConfig": map[string]int{"maxOutputTokens": maxTokens},
	}
	if system != "" {
		reqBody["systemInstruction"] = content{Parts: []part{{Text: system}}}
	}
	body, _ := json.Marshal(reqBody)

	url := "https://generativelanguage.googleapis.com/v1beta/models/" + model +
		":generateContent?key=" + apiKey
	req, _ := http.NewRequest("POST", url, bytes.NewReader(body))
	req.Header.Set("Content-Type", "application/json")

	resp, err := http.DefaultClient.Do(req)
	if err != nil {
		return "", 0, 0, &retryableErr{fmt.Errorf("gemini: %w", err)}
	}
	defer resp.Body.Close()
	if resp.StatusCode == 429 || resp.StatusCode >= 500 {
		b, _ := io.ReadAll(resp.Body)
		return "", 0, 0, &retryableErr{fmt.Errorf("gemini HTTP %d: %s", resp.StatusCode, b)}
	}
	var result struct {
		Candidates []struct {
			Content content `json:"content"`
		} `json:"candidates"`
		UsageMetadata *struct {
			PromptTokenCount     int `json:"promptTokenCount"`
			CandidatesTokenCount int `json:"candidatesTokenCount"`
		} `json:"usageMetadata"`
		Error *struct{ Message string `json:"message"` } `json:"error"`
	}
	if err := json.NewDecoder(resp.Body).Decode(&result); err != nil {
		return "", 0, 0, fmt.Errorf("gemini parse: %w", err)
	}
	if result.Error != nil {
		return "", 0, 0, fmt.Errorf("gemini: %s", result.Error.Message)
	}
	if len(result.Candidates) == 0 || len(result.Candidates[0].Content.Parts) == 0 {
		return "", 0, 0, fmt.Errorf("gemini: empty response")
	}
	var in, out int
	if result.UsageMetadata != nil {
		in = result.UsageMetadata.PromptTokenCount
		out = result.UsageMetadata.CandidatesTokenCount
	}
	return result.Candidates[0].Content.Parts[0].Text, in, out, nil
}

// ---------------------------------------------------------------------------
// Logging
// ---------------------------------------------------------------------------

type llmLogEntry struct {
	Provider     string `json:"provider"`
	TaskID       string `json:"taskId,omitempty"`
	Agent        string `json:"agent"`
	Model        string `json:"model"`
	StartedAt    string `json:"startedAt"`
	DurationMs   int64  `json:"durationMs"`
	InputTokens  int    `json:"inputTokens,omitempty"`
	OutputTokens int    `json:"outputTokens,omitempty"`
	Status       string `json:"status"`
	Error        string `json:"error,omitempty"`
}

func writeLLMLog(logDir string, entry llmLogEntry) {
	if err := os.MkdirAll(logDir, 0o755); err != nil {
		return
	}
	ts := strings.NewReplacer(":", "-", ".", "-").Replace(time.Now().UTC().Format(time.RFC3339Nano))
	task := entry.TaskID
	if task == "" {
		task = "no-task"
	}
	name := strings.ReplaceAll(task+"-"+entry.Agent+"-"+ts+".json", "/", "_")
	data, _ := json.MarshalIndent(entry, "", "  ")
	_ = os.WriteFile(filepath.Join(logDir, name), data, 0o644)
}

func llmStatus(err error) string {
	if err == nil {
		return "ok"
	}
	return "failed"
}

func llmErrStr(err error) string {
	if err == nil {
		return ""
	}
	return err.Error()
}
