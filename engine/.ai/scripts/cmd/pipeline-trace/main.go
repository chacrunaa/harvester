// Command pipeline-trace прогоняет настоящий движок конвейера и
// записывает журнал переходов в JSON для статичной витрины (ui/).
//
// Что здесь настоящее: PipelineWatcher со своим fsnotify, порядок фаз,
// AND-гейты и переключение фаз — ровно тот код, который работает в
// бэкенде. Подменён только запуск агента: вместо вызова LLM коллбэк
// TriggerAgent сразу помечает агента завершённым. Поэтому трассировка
// не требует ключей и не ходит в сеть.
//
//	go run ./cmd/pipeline-trace -out ../../../ui/data/engine-run.js
package main

import (
	"encoding/json"
	"flag"
	"fmt"
	"os"
	"path/filepath"
	"sort"
	"sync"
	"time"

	scripts "harvester/scripts"
)

const taskID = "DEMO-001"

// event — одна запись журнала для витрины.
type event struct {
	Seq     int               `json:"seq"`
	Kind    string            `json:"kind"`
	Phase   string            `json:"phase,omitempty"`
	Agent   string            `json:"agent,omitempty"`
	From    string            `json:"from,omitempty"`
	To      string            `json:"to,omitempty"`
	Note    string            `json:"note,omitempty"`
	Agents  map[string]string `json:"agents,omitempty"`
	Elapsed int64             `json:"elapsed_ms"`
}

type recorder struct {
	mu     sync.Mutex
	events []event
	start  time.Time
	done   chan struct{}
	closed bool
}

func (r *recorder) add(e event) {
	r.mu.Lock()
	defer r.mu.Unlock()
	e.Seq = len(r.events) + 1
	e.Elapsed = time.Since(r.start).Milliseconds()
	r.events = append(r.events, e)
	fmt.Printf("  %2d  %-16s %s%s%s\n", e.Seq, e.Kind, e.Agent, e.Phase, e.To)
}

func (r *recorder) finish() {
	r.mu.Lock()
	defer r.mu.Unlock()
	if !r.closed {
		r.closed = true
		close(r.done)
	}
}

func (r *recorder) isDone() bool {
	r.mu.Lock()
	defer r.mu.Unlock()
	return r.closed
}

// waitForPhase ждёт, пока движок переведёт конвейер на нужную фазу.
func waitForPhase(aiDir, phase string, timeout time.Duration) bool {
	deadline := time.Now().Add(timeout)
	for time.Now().Before(deadline) {
		raw, err := os.ReadFile(filepath.Join(aiDir, "pipeline-state.json"))
		if err == nil {
			var s scripts.PipelineState
			if json.Unmarshal(raw, &s) == nil && s.Phase == phase {
				return true
			}
		}
		time.Sleep(100 * time.Millisecond)
	}
	return false
}

// phases в том порядке, в котором их обходит движок, вместе с составом
// агентов — используется только для последовательной отметки ролей.
var phases = []struct {
	name         string
	orchestrator string
	parallel     []string
	tail         []string
}{
	{"business", "product-manager",
		[]string{"product-analyst", "market-analyst", "strategist", "financier"}, nil},
	{"systemic", "owner", []string{"analyst", "architect"}, nil},
	{"development", "dev-lead", []string{"backend", "frontend"}, []string{"reviewers"}},
	{"testing", "qa-lead", []string{"qa", "penetration"}, nil},
}

func main() {
	out := flag.String("out", "engine-run.js", "куда записать JS с трассировкой")
	flag.Parse()

	tmp, err := os.MkdirTemp("", "pipeline-trace-")
	must(err)
	defer os.RemoveAll(tmp)

	aiDir := filepath.Join(tmp, ".ai")
	must(os.MkdirAll(filepath.Join(aiDir, "chats"), 0o755))

	// Начальное состояние: все агенты pending, первая рабочая фаза.
	// Фаза обязана быть из phaseOrder — для "init" оркестратор не
	// определён и движок переходов не делает.
	state := scripts.PipelineState{
		TaskID: taskID,
		Phase:  "business",
		Agents: map[string]string{},
	}
	for _, p := range phases {
		state.Agents[p.orchestrator] = "pending"
		for _, a := range p.parallel {
			state.Agents[a] = "pending"
		}
		for _, a := range p.tail {
			state.Agents[a] = "pending"
		}
	}
	state.Agents["office-manager"] = "pending"
	writeState(aiDir, &state)

	rec := &recorder{start: time.Now(), done: make(chan struct{})}

	watcher := scripts.NewWatcher(aiDir, scripts.WatcherCallbacks{
		TriggerAgent: func(agentID, task string) {
			rec.add(event{Kind: "agent_triggered", Agent: agentID,
				Note: "движок запросил запуск агента"})
		},
		OnStateChanged: func(s *scripts.PipelineState) {
			rec.add(event{Kind: "state_changed", Phase: s.Phase,
				Agents: copyAgents(s.Agents)})
		},
		OnPhaseAdvanced: func(task, from, to string) {
			rec.add(event{Kind: "phase_advanced", From: from, To: to,
				Note: "оркестратор фазы завершил работу"})
		},
		OnAgentFailed: func(task, phase, agent string) {
			rec.add(event{Kind: "agent_failed", Phase: phase, Agent: agent})
		},
		OnPipelineComplete: func(task string) {
			rec.add(event{Kind: "pipeline_complete", Note: "все фазы пройдены"})
			rec.finish()
		},
		OnQnaPending: func(path string) {
			rec.add(event{Kind: "qna_pending", Note: path})
		},
		OnFileChanged: func(path string) {},
	})

	watcher.Start()
	defer watcher.Stop()

	fmt.Println("Прогон движка в", aiDir)
	rec.add(event{Kind: "pipeline_start", Phase: "init",
		Note: fmt.Sprintf("задача %s, %d агентов", taskID, len(state.Agents))})

	// Движок сам переключает фазы, когда завершается оркестратор фазы.
	// Поэтому драйвер реактивный: ждём, пока движок встанет на нужную
	// фазу, и только тогда отмечаем её агентов — как это делал бы
	// настоящий агент, записывая статус в pipeline-state.json.
	for _, p := range phases {
		if !waitForPhase(aiDir, p.name, 10*time.Second) {
			rec.add(event{Kind: "trace_error",
				Note: "движок не перешёл на фазу " + p.name})
			break
		}
		rec.add(event{Kind: "phase_active", Phase: p.name,
			Note: "оркестратор фазы — " + p.orchestrator})

		for _, a := range p.parallel {
			setAgent(aiDir, rec, a, scripts.StatusInProgress,
				"параллельная ветка фазы "+p.name)
		}
		// AND-гейт пропускает дальше только когда все ветки done.
		for i, a := range p.parallel {
			note := "ветка завершена, AND-гейт ещё держит фазу"
			if i == len(p.parallel)-1 {
				note = "последняя ветка — AND-гейт открывается"
			}
			setAgent(aiDir, rec, a, scripts.StatusDone, note)
		}
		for _, a := range p.tail {
			setAgent(aiDir, rec, a, scripts.StatusDone,
				"запущен AND-гейтом фазы "+p.name)
		}
		// Оркестратор завершается последним — это и двигает фазу.
		setAgent(aiDir, rec, p.orchestrator, scripts.StatusDone,
			"оркестратор фазы "+p.name+" закончил: фаза может двигаться")

		if rec.isDone() {
			break
		}
	}

	if !rec.isDone() {
		setAgent(aiDir, rec, "office-manager", scripts.StatusDone, "завершение конвейера")
	}

	select {
	case <-rec.done:
	case <-time.After(5 * time.Second):
		rec.add(event{Kind: "trace_end", Note: "журнал закрыт по таймауту"})
	}

	payload := map[string]any{
		"title":    "Прогон движка конвейера",
		"subtitle": "Записан настоящим PipelineWatcher: порядок фаз, AND-гейты и переключение фаз — рабочий код. Вызовы LLM не выполнялись.",
		"task":     taskID,
		"phases":   []string{"business", "systemic", "development", "testing"},
		"events":   rec.events,
	}
	body, err := json.MarshalIndent(payload, "", "  ")
	must(err)

	must(os.MkdirAll(filepath.Dir(*out), 0o755))
	content := "// Сгенерировано .ai/scripts/cmd/pipeline-trace на реальном прогоне движка. Не редактировать вручную.\n" +
		"window.__ENGINE_RUN__ = " + string(body) + ";\n"
	must(os.WriteFile(*out, []byte(content), 0o644))

	fmt.Printf("\nЗаписано: %s (%d событий)\n", *out, len(rec.events))
}

// setAgent пишет статус агента в pipeline-state.json — ровно то, что
// делает настоящий агент. Дальше движок реагирует сам через fsnotify.
func setAgent(aiDir string, rec *recorder, agent, status, note string) {
	path := filepath.Join(aiDir, "pipeline-state.json")
	raw, err := os.ReadFile(path)
	must(err)
	var s scripts.PipelineState
	must(json.Unmarshal(raw, &s))
	s.Agents[agent] = status
	writeState(aiDir, &s)

	rec.add(event{Kind: "agent_" + status, Agent: agent, Phase: s.Phase, Note: note})
	// У watcher'а дебаунс 300 мс, причём таймер сбрасывается на каждом
	// новом событии. Ждём заведомо дольше, иначе несколько записей
	// склеятся в один вызов и переходы фаз не отработают по одному.
	time.Sleep(450 * time.Millisecond)
}

func writeState(aiDir string, s *scripts.PipelineState) {
	body, err := json.MarshalIndent(s, "", "  ")
	must(err)
	must(os.WriteFile(filepath.Join(aiDir, "pipeline-state.json"), body, 0o644))
}

func copyAgents(in map[string]string) map[string]string {
	out := make(map[string]string, len(in))
	keys := make([]string, 0, len(in))
	for k := range in {
		keys = append(keys, k)
	}
	sort.Strings(keys)
	for _, k := range keys {
		out[k] = in[k]
	}
	return out
}

func must(err error) {
	if err != nil {
		fmt.Fprintln(os.Stderr, "ошибка:", err)
		os.Exit(1)
	}
}
