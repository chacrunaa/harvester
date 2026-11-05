package transport

import (
	"fmt"
	"log"
	"path/filepath"

	"github.com/gin-gonic/gin"

	"harvester/backend/internal/constants"
	"harvester/backend/internal/service"
	handlers "harvester/backend/internal/transport/http"
	"harvester/backend/internal/transport/ws"
)

func NewRouter(tc *handlers.Container, hub *service.Hub) *gin.Engine {
	r := gin.Default()
	r.Use(corsMiddleware())

	// Liveness-проба для Docker HEALTHCHECK и Caddy (health_uri /health).
	r.GET(constants.RouteHealth, func(c *gin.Context) {
		c.JSON(200, gin.H{"status": "ok"})
	})

	r.GET(constants.RouteWS, func(c *gin.Context) {
		ws.ServeWS(hub, c.Writer, c.Request)
	})

	api := r.Group(constants.RouteAPI)
	{
		api.GET(constants.RoutePipelineState, tc.Pipeline.GetState)
		api.POST(constants.RoutePipelinePhaseOk, tc.Pipeline.PhaseOk)
		api.POST(constants.RoutePipelinePhaseNotOk, tc.Pipeline.PhaseNotOk)
		api.POST(constants.RoutePipelineAgentRetry, tc.Pipeline.AgentRetry)
		api.POST(constants.RoutePipelineAgentSkip, tc.Pipeline.AgentSkip)

		api.GET(constants.RouteProjects, tc.Projects.List)
		api.POST(constants.RouteProjectsOpen, tc.Projects.Open)
		api.POST(constants.RouteProjectsCreate, tc.Projects.Create)

		api.GET(constants.RouteQnaPending, tc.Qna.ListPending)
		api.POST(constants.RouteQnaAnswer, tc.Qna.Answer)

		api.GET(constants.RouteChats, tc.Chats.Get)
		api.POST(constants.RouteChats, tc.Chats.Post)

		api.POST(constants.RouteAgentsTrigger, tc.Agents.Trigger)

		api.GET(constants.RouteTasks, tc.Tasks.List)

		api.GET(constants.RouteSettings, tc.Settings.Get)
		api.POST(constants.RouteSettings, tc.Settings.Update)
	}

	return r
}

func Serve(port string, c *service.Container, rootDir string) {
	router := NewRouter(handlers.NewContainer(c, filepath.Join(rootDir, constants.DirTemplates)), c.Hub)
	addr := fmt.Sprintf(":%s", port)
	log.Printf("harvester backend listening on %s", addr)
	if err := router.Run(addr); err != nil {
		log.Fatalf("server error: %v", err)
	}
}

func corsMiddleware() gin.HandlerFunc {
	return func(c *gin.Context) {
		c.Header("Access-Control-Allow-Origin", constants.CORSAllowOrigin)
		c.Header("Access-Control-Allow-Methods", constants.CORSAllowMethods)
		c.Header("Access-Control-Allow-Headers", constants.CORSAllowHeaders)
		if c.Request.Method == "OPTIONS" {
			c.AbortWithStatus(204)
			return
		}
		c.Next()
	}
}
