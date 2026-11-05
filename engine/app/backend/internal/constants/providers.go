package constants

// Provider type and canonical identifiers.
type Provider = string

const (
	ProviderClaude   Provider = "claude"
	ProviderCodex    Provider = "codex"
	ProviderDeepSeek Provider = "deepseek"
	ProviderGemini   Provider = "gemini"
)

// ValidProviders is the full list of supported LLM providers.
var ValidProviders = []Provider{ProviderClaude, ProviderCodex, ProviderDeepSeek, ProviderGemini}

// Non-canonical names accepted in config.
const (
	ProviderAliasAnthropic = "anthropic"
	ProviderAliasOpenAI    = "openai"
)

// ProviderEnvKey maps each provider to its API key environment variable.
var ProviderEnvKey = map[Provider]string{
	ProviderClaude:   EnvAnthropicAPIKey,
	ProviderCodex:    EnvOpenAIAPIKey,
	ProviderDeepSeek: EnvDeepSeekAPIKey,
	ProviderGemini:   EnvGeminiAPIKey,
}

// ProviderDefaultModel maps each provider to its default model identifier.
var ProviderDefaultModel = map[Provider]string{
	ProviderClaude:   DefaultModelClaude,
	ProviderCodex:    DefaultModelCodex,
	ProviderDeepSeek: DefaultModelDeepSeek,
	ProviderGemini:   DefaultModelGemini,
}
