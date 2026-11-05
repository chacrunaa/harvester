package constants

// AgentStatus and pipeline phase statuses.
type AgentStatus = string

const (
	StatusWaiting    AgentStatus = "waiting"
	StatusInProgress AgentStatus = "in-progress"
	StatusDone       AgentStatus = "done"
	StatusFailed     AgentStatus = "failed"
	StatusPending    AgentStatus = "pending"
)

// ID and timestamp formats.
const (
	FmtTaskID         = "task-%d"
	FmtMessageID      = "msg-%d"
	FmtPipelineTaskID = "TF-%s"
	LayoutTaskID      = "200601021504"
)

// Domain roles and default statuses.
const (
	TaskStatusOpen = "open"
	ChatRoleAgent  = "agent"
)
