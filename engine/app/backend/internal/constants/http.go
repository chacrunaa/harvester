package constants

// API route paths.
const (
	RouteWS     = "/ws"
	RouteAPI    = "/api"
	RouteHealth = "/health"

	RoutePipelineState      = "/pipeline/state"
	RoutePipelinePhaseOk    = "/pipeline/phase/:phase/ok"
	RoutePipelinePhaseNotOk = "/pipeline/phase/:phase/notok"
	RoutePipelineAgentRetry = "/pipeline/agent/:agentName/retry"
	RoutePipelineAgentSkip  = "/pipeline/agent/:agentName/skip"

	RouteProjects       = "/projects"
	RouteProjectsOpen   = "/projects/open"
	RouteProjectsCreate = "/projects/create"

	RouteQnaPending = "/qna/pending"
	RouteQnaAnswer  = "/qna/:agentId/answer"

	RouteChats = "/chats/:phase"

	RouteAgentsTrigger = "/agents/:agentId/trigger"

	RouteTasks = "/tasks"

	RouteSettings = "/settings"
)

// CORS policy values.
const (
	CORSAllowOrigin  = "*"
	CORSAllowMethods = "GET, POST, PUT, DELETE, OPTIONS"
	CORSAllowHeaders = "Content-Type, Authorization"
)
