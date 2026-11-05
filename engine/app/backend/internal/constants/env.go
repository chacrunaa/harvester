package constants

// Environment variable names.
const (
	EnvRootDir     = "ROOT_DIR"
	EnvPort        = "PORT"
	EnvAIDir       = "AI_DIR"
	EnvPoligonsDir = "POLIGONS_DIR"
	EnvLLMProvider = "LLM_PROVIDER"

	EnvAnthropicAPIKey = "ANTHROPIC_API_KEY"
	EnvOpenAIAPIKey    = "OPENAI_API_KEY"
	EnvDeepSeekAPIKey  = "DEEPSEEK_API_KEY"
	EnvGeminiAPIKey    = "GEMINI_API_KEY"

	EnvAnthropicModel = "ANTHROPIC_MODEL"
	EnvOpenAIModel    = "OPENAI_MODEL"
	EnvDeepSeekModel  = "DEEPSEEK_MODEL"
	EnvGeminiModel    = "GEMINI_MODEL"
)

// Default values.
const (
	DefaultPort = "3100"
)

// Default model identifiers per provider.
const (
	DefaultModelClaude   = "claude-sonnet-4-6"
	DefaultModelCodex    = "gpt-4o"
	DefaultModelDeepSeek = "deepseek-chat"
	DefaultModelGemini   = "gemini-2.0-flash"
)
