package constants

// WebSocket event types.
const (
	EventPipelineStateChanged = "pipeline:state_changed"
	EventIncidentNew          = "incident:new"
	EventPipelinePhaseDone    = "pipeline:phase_done"
	EventPipelineCompleted    = "pipeline:completed"
	EventAgentQnaWaiting      = "agent:qna_waiting"
	EventBriefReady           = "brief:ready"
)

// Watcher file-matching patterns.
const (
	ExtMarkdown = ".md"
	KeyBrief    = "brief"
)
