package bootstrap

import (
	"harvester/backend/internal/config"
	"harvester/backend/internal/service"
	"harvester/backend/internal/transport"
)

func Run() {
	rootDir := config.ResolveRootDir()
	config.LoadEnv(rootDir)
	cfg := config.Load(rootDir)
	c := service.NewContainer(cfg)
	c.Watcher.Start()
	transport.Serve(cfg.Server.Port, c, rootDir)
}
