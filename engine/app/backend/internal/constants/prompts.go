package constants

// PromptAgentSystem is the system prompt template for agent chat sessions.
const PromptAgentSystem = "Ты агент с ролью %s. Отвечай на русском языке."

// PhaseAgents maps each pipeline phase to its participant agents.
var PhaseAgents = map[string][]string{
	"business":    {"product-manager", "product-analyst", "market-analyst", "strategist", "financier"},
	"systemic":    {"owner", "architect", "analyst"},
	"development": {"dev-lead", "backend", "frontend", "reviewers"},
	"testing":     {"qa-lead", "qa", "penetration"},
}
