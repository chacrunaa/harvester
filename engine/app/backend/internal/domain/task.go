package domain

type Task struct {
	ID          string `json:"id"`
	Title       string `json:"title"`
	Description string `json:"description,omitempty"`
	Status      string `json:"status"`
	CreatedAt   string `json:"createdAt"`
}

type TasksFile struct {
	Tasks []Task `json:"tasks"`
}
