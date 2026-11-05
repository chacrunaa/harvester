package service

import (
	"fmt"
	"os"
	"sync"

	"harvester/backend/internal/constants"
	"harvester/backend/internal/domain"
)


type settingsService struct {
	mu       sync.RWMutex
	provider constants.Provider
	keys     map[constants.Provider]string
	models   map[constants.Provider]string
}

func NewSettingsService(llmProvider string, models map[constants.Provider]string) *settingsService {
	s := &settingsService{
		provider: constants.ProviderClaude,
		keys:     make(map[constants.Provider]string),
		models:   models,
	}
	if s.models == nil {
		s.models = make(map[constants.Provider]string)
	}
	switch llmProvider {
	case constants.ProviderAliasAnthropic, constants.ProviderClaude:
		s.provider = constants.ProviderClaude
	case constants.ProviderAliasOpenAI, constants.ProviderCodex:
		s.provider = constants.ProviderCodex
	case constants.ProviderGemini:
		s.provider = constants.ProviderGemini
	case constants.ProviderDeepSeek:
		s.provider = constants.ProviderDeepSeek
	}
	for _, p := range constants.ValidProviders {
		if envKey, ok := constants.ProviderEnvKey[p]; ok {
			if v := os.Getenv(envKey); v != "" {
				s.keys[p] = v
			}
		}
	}
	return s
}

func (s *settingsService) snapshot() domain.SettingsSnapshot {
	status := make(map[string]bool)
	for _, p := range constants.ValidProviders {
		status[p] = s.keys[p] != "" || os.Getenv(constants.ProviderEnvKey[p]) != ""
	}
	return domain.SettingsSnapshot{Provider: s.provider, KeyStatus: status}
}

func (s *settingsService) Snapshot() domain.SettingsSnapshot {
	s.mu.RLock()
	defer s.mu.RUnlock()
	return s.snapshot()
}

func (s *settingsService) Update(provider, apiKey string) (domain.SettingsSnapshot, error) {
	s.mu.Lock()
	defer s.mu.Unlock()

	if provider != "" {
		valid := false
		for _, p := range constants.ValidProviders {
			if p == provider {
				valid = true
				break
			}
		}
		if !valid {
			return domain.SettingsSnapshot{}, fmt.Errorf("invalid provider: %s", provider)
		}
		s.provider = provider
		os.Setenv(constants.EnvLLMProvider, provider)
	}
	if apiKey != "" {
		s.keys[s.provider] = apiKey
		if envKey, ok := constants.ProviderEnvKey[s.provider]; ok {
			os.Setenv(envKey, apiKey)
		}
	}
	return s.snapshot(), nil
}

func (s *settingsService) ActiveAPIKey() string {
	s.mu.RLock()
	defer s.mu.RUnlock()
	p := s.provider
	if k := s.keys[p]; k != "" {
		return k
	}
	if envKey, ok := constants.ProviderEnvKey[p]; ok {
		return os.Getenv(envKey)
	}
	return ""
}

func (s *settingsService) ActiveProvider() string {
	s.mu.RLock()
	defer s.mu.RUnlock()
	return s.provider
}

func (s *settingsService) ActiveModel() string {
	s.mu.RLock()
	defer s.mu.RUnlock()
	if m := s.models[s.provider]; m != "" {
		return m
	}
	return constants.ProviderDefaultModel[s.provider]
}
