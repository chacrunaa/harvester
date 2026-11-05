package transport

import (
	"encoding/json"
	"net/http"
	"net/http/httptest"
	"testing"

	"github.com/gin-gonic/gin"

	"harvester/backend/internal/config"
	"harvester/backend/internal/constants"
	"harvester/backend/internal/service"
	handlers "harvester/backend/internal/transport/http"
)

// newTestRouter собирает роутер на временном каталоге: конструкторы
// сервисов не трогают диск и не поднимают горутин, поэтому хватает
// пустого конфига.
func newTestRouter(t *testing.T) *gin.Engine {
	t.Helper()
	gin.SetMode(gin.TestMode)

	root := t.TempDir()
	cfg := &config.Config{
		Server: config.ServerConfig{Port: constants.DefaultPort},
		Paths:  config.PathsConfig{RootDir: root},
		LLM:    config.LLMConfig{Provider: string(constants.ProviderClaude)},
	}

	c := service.NewContainer(cfg)
	return NewRouter(handlers.NewContainer(c, root), c.Hub)
}

func TestHealthEndpoint(t *testing.T) {
	router := newTestRouter(t)

	req := httptest.NewRequest(http.MethodGet, constants.RouteHealth, nil)
	rec := httptest.NewRecorder()
	router.ServeHTTP(rec, req)

	if rec.Code != http.StatusOK {
		t.Fatalf("GET %s = %d, want %d", constants.RouteHealth, rec.Code, http.StatusOK)
	}

	var body map[string]string
	if err := json.Unmarshal(rec.Body.Bytes(), &body); err != nil {
		t.Fatalf("ответ не является JSON: %v (тело: %q)", err, rec.Body.String())
	}
	if body["status"] != "ok" {
		t.Errorf(`status = %q, want "ok"`, body["status"])
	}
}

// Docker HEALTHCHECK и Caddy (health_uri) обращаются к /health без
// префикса /api — проверяем, что он не уехал под группу.
func TestHealthIsNotUnderAPIPrefix(t *testing.T) {
	router := newTestRouter(t)

	req := httptest.NewRequest(http.MethodGet, constants.RouteAPI+constants.RouteHealth, nil)
	rec := httptest.NewRecorder()
	router.ServeHTTP(rec, req)

	if rec.Code != http.StatusNotFound {
		t.Errorf("GET /api/health = %d, want %d", rec.Code, http.StatusNotFound)
	}
}

func TestCORSHeadersAndPreflight(t *testing.T) {
	router := newTestRouter(t)

	req := httptest.NewRequest(http.MethodOptions, constants.RouteHealth, nil)
	rec := httptest.NewRecorder()
	router.ServeHTTP(rec, req)

	if rec.Code != http.StatusNoContent {
		t.Errorf("OPTIONS %s = %d, want %d", constants.RouteHealth, rec.Code, http.StatusNoContent)
	}
	if got := rec.Header().Get("Access-Control-Allow-Origin"); got != constants.CORSAllowOrigin {
		t.Errorf("Access-Control-Allow-Origin = %q, want %q", got, constants.CORSAllowOrigin)
	}
}

// Карта маршрутов — страховка от переименования констант: если путь
// изменится, фронтенд и инфраструктура сломаются молча.
func TestExpectedRoutesAreRegistered(t *testing.T) {
	router := newTestRouter(t)

	registered := make(map[string]bool)
	for _, r := range router.Routes() {
		registered[r.Method+" "+r.Path] = true
	}

	want := []string{
		"GET " + constants.RouteHealth,
		"GET " + constants.RouteWS,
		"GET " + constants.RouteAPI + constants.RoutePipelineState,
		"POST " + constants.RouteAPI + constants.RoutePipelinePhaseOk,
		"POST " + constants.RouteAPI + constants.RoutePipelinePhaseNotOk,
		"POST " + constants.RouteAPI + constants.RoutePipelineAgentRetry,
		"POST " + constants.RouteAPI + constants.RoutePipelineAgentSkip,
		"GET " + constants.RouteAPI + constants.RouteProjects,
		"POST " + constants.RouteAPI + constants.RouteProjectsOpen,
		"POST " + constants.RouteAPI + constants.RouteProjectsCreate,
		"GET " + constants.RouteAPI + constants.RouteQnaPending,
		"POST " + constants.RouteAPI + constants.RouteQnaAnswer,
		"GET " + constants.RouteAPI + constants.RouteChats,
		"POST " + constants.RouteAPI + constants.RouteChats,
		"POST " + constants.RouteAPI + constants.RouteAgentsTrigger,
		"GET " + constants.RouteAPI + constants.RouteTasks,
		"GET " + constants.RouteAPI + constants.RouteSettings,
		"POST " + constants.RouteAPI + constants.RouteSettings,
	}

	for _, route := range want {
		if !registered[route] {
			t.Errorf("маршрут не зарегистрирован: %s", route)
		}
	}
}
