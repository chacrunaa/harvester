package config

type Config struct {
	Server ServerConfig
	Paths  PathsConfig
	LLM    LLMConfig
}

type ServerConfig struct {
	Port string
}

type PathsConfig struct {
	RootDir      string
	AiDir        string
	HarvestAiDir string
	ScriptsDir   string
	AgentsDir    string
	StubsDir     string
	PoligonsDir  string
}

type LLMConfig struct {
	Provider string
	Models   LLMModels
}

type LLMModels struct {
	Anthropic string
	OpenAI    string
	DeepSeek  string
	Gemini    string
}
