package domain

type ChatMessage struct {
	ID        string `json:"id,omitempty"`
	Type      string `json:"type"`
	Role      string `json:"role,omitempty"`
	Agent     string `json:"agent,omitempty"`
	Content   string `json:"content"`
	Timestamp string `json:"timestamp"`
	ChatID    string `json:"chatId,omitempty"`
	Mentions  []string `json:"mentions,omitempty"`
}
