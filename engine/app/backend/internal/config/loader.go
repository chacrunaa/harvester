package config

import (
	"os"
	"path/filepath"

	"github.com/joho/godotenv"

	"harvester/backend/internal/constants"
)

func LoadEnv(rootDir string) {
	_ = godotenv.Load(filepath.Join(rootDir, constants.DirApp, constants.DirBackend, constants.FileEnv))
	_ = godotenv.Load(filepath.Join(rootDir, constants.FileEnv))
}

func ResolveRootDir() string {
	if v := os.Getenv(constants.EnvRootDir); v != "" {
		return v
	}
	cwd, err := os.Getwd()
	if err != nil {
		return "."
	}
	dir := cwd
	for {
		if _, err := os.Stat(filepath.Join(dir, constants.FileGoMod)); err == nil {
			return filepath.Join(dir, "..", "..")
		}
		parent := filepath.Dir(dir)
		if parent == dir {
			break
		}
		dir = parent
	}
	return cwd
}

func Load(rootDir string) *Config {
	return &Config{
		Server: ServerConfig{
			Port: getEnv(constants.EnvPort, constants.DefaultPort),
		},
		Paths: PathsConfig{
			RootDir:      rootDir,
			AiDir:        getEnv(constants.EnvAIDir, ""),
			HarvestAiDir: filepath.Join(rootDir, constants.DirAI),
			ScriptsDir:   filepath.Join(rootDir, constants.DirAI, constants.DirScripts),
			AgentsDir:    filepath.Join(rootDir, constants.DirAI, constants.DirAgents),
			StubsDir:     filepath.Join(rootDir, constants.DirApp, constants.DirStubs),
			PoligonsDir:  getEnv(constants.EnvPoligonsDir, filepath.Join(rootDir, constants.DirPoligons)),
		},
		LLM: LLMConfig{
			Provider: getEnv(constants.EnvLLMProvider, constants.ProviderClaude),
			Models: LLMModels{
				Anthropic: getEnv(constants.EnvAnthropicModel, constants.DefaultModelClaude),
				OpenAI:    getEnv(constants.EnvOpenAIModel, constants.DefaultModelCodex),
				DeepSeek:  getEnv(constants.EnvDeepSeekModel, constants.DefaultModelDeepSeek),
				Gemini:    getEnv(constants.EnvGeminiModel, constants.DefaultModelGemini),
			},
		},
	}
}

func getEnv(key, fallback string) string {
	if v := os.Getenv(key); v != "" {
		return v
	}
	return fallback
}