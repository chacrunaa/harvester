package domain

type AgentRunResult struct {
	Status string `json:"status"`
	Error  string `json:"error,omitempty"`
}
