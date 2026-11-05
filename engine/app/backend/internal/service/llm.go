package service

import (
	"time"

	scriptslib "harvester/scripts/lib"
)

// llmCallOptions are optional parameters for a single LLM call.
type llmCallOptions struct {
	MaxTokens int
	TaskID    string
	Agent     string
	LogDir    string
	Retries   int
	BaseDelay time.Duration
}

// llmService wraps the scripts/lib LLM engine, providing provider config from settingsService.
type llmService struct {
	settings *settingsService
}

func NewLlmService(settings *settingsService) *llmService {
	return &llmService{settings: settings}
}

// Generate sends a prompt to the configured LLM and returns the response text.
func (s *llmService) Generate(system, userPrompt string) (string, error) {
	return s.Call(system, userPrompt, llmCallOptions{})
}

// Call is the full form with per-call options.
func (s *llmService) Call(system, userPrompt string, opts llmCallOptions) (string, error) {
	return scriptslib.Call(s.config(opts), system, userPrompt, scriptslib.CallOpts{
		TaskID: opts.TaskID,
		Agent:  opts.Agent,
		LogDir: opts.LogDir,
	})
}

// Config returns the scripts/lib.Config populated from active settings + call options.
func (s *llmService) Config(opts llmCallOptions) scriptslib.Config {
	return s.config(opts)
}

func (s *llmService) config(opts llmCallOptions) scriptslib.Config {
	maxTokens := opts.MaxTokens
	if maxTokens == 0 {
		maxTokens = scriptslib.DefaultMaxTokens
	}
	retries := opts.Retries
	if retries == 0 {
		retries = scriptslib.DefaultRetries
	}
	baseDelay := opts.BaseDelay
	if baseDelay == 0 {
		baseDelay = scriptslib.DefaultBaseDelay
	}
	return scriptslib.Config{
		Provider:  s.settings.ActiveProvider(),
		APIKey:    s.settings.ActiveAPIKey(),
		Model:     s.settings.ActiveModel(),
		MaxTokens: maxTokens,
		Retries:   retries,
		BaseDelay: baseDelay,
	}
}
