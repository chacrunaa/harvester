package domain

type ProjectListEntry struct {
	Name string `json:"name"`
	Path string `json:"path"`
}

type ProjectInfo struct {
	ID     string         `json:"id"`
	Label  string         `json:"label"`
	AiDir  string         `json:"aiDir"`
	Active bool           `json:"active"`
	State  *PipelineState `json:"state"`
}
