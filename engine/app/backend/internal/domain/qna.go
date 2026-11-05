package domain

type QnaQuestion struct {
	ID       string `json:"id"`
	Question string `json:"question"`
	Answer   string `json:"answer"`
}

type PendingQna struct {
	AgentID   string        `json:"agentId"`
	TaskID    string        `json:"taskId"`
	Questions []QnaQuestion `json:"questions"`
}

type QnaAnswer struct {
	ID     string `json:"id"`
	Answer string `json:"answer"`
}
