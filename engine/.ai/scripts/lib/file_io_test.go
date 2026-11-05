package lib

import (
	"os"
	"path/filepath"
	"testing"
)

func TestWriteAtomic_CreatesFile(t *testing.T) {
	dir := t.TempDir()
	path := filepath.Join(dir, "output.txt")

	if err := WriteAtomic(path, "hello world"); err != nil {
		t.Fatalf("WriteAtomic failed: %v", err)
	}
	data, err := os.ReadFile(path)
	if err != nil {
		t.Fatalf("file not created: %v", err)
	}
	if string(data) != "hello world" {
		t.Errorf("content mismatch: got %q", string(data))
	}
	if _, err := os.Stat(path + ".tmp"); err == nil {
		t.Error(".tmp file should be removed after atomic write")
	}
}

func TestWriteAtomic_CreatesParentDirs(t *testing.T) {
	dir := t.TempDir()
	path := filepath.Join(dir, "sub", "deep", "file.txt")
	if err := WriteAtomic(path, "content"); err != nil {
		t.Fatalf("WriteAtomic should create parent dirs: %v", err)
	}
	if _, err := os.Stat(path); err != nil {
		t.Error("file not created inside new subdirectories")
	}
}

func TestCopyAtomic_CopiesContent(t *testing.T) {
	dir := t.TempDir()
	src := filepath.Join(dir, "src.txt")
	dst := filepath.Join(dir, "subdir", "dst.txt")

	if err := os.WriteFile(src, []byte("routed content"), 0o644); err != nil {
		t.Fatal(err)
	}
	if !copyAtomic(src, dst) {
		t.Fatal("copyAtomic returned false")
	}
	data, err := os.ReadFile(dst)
	if err != nil || string(data) != "routed content" {
		t.Errorf("copyAtomic content mismatch: %v", err)
	}
	if _, err := os.Stat(dst + ".tmp"); err == nil {
		t.Error(".tmp file should be removed after atomic copy")
	}
}

func TestCopyAtomic_MissingSource(t *testing.T) {
	dir := t.TempDir()
	if copyAtomic(filepath.Join(dir, "nope.txt"), filepath.Join(dir, "out.txt")) {
		t.Error("expected false for missing source")
	}
}

func TestApplyRouting_CopiesFile(t *testing.T) {
	dir := t.TempDir()
	src := filepath.Join(dir, "src.md")
	if err := os.WriteFile(src, []byte("# routed"), 0o644); err != nil {
		t.Fatal(err)
	}

	rules := []RoutingRule{
		{From: "src.md", To: filepath.Join("deep", "dst.md")},
	}
	results := ApplyRouting(rules, dir)

	if len(results) != 1 {
		t.Fatalf("expected 1 result, got %d", len(results))
	}
	if !results[0].OK {
		t.Error("routing failed")
	}
	data, err := os.ReadFile(filepath.Join(dir, "deep", "dst.md"))
	if err != nil || string(data) != "# routed" {
		t.Errorf("routed file content mismatch: %v", err)
	}
}

func TestLoadAllRoutes_EmptyDir(t *testing.T) {
	dir := t.TempDir()
	routes := LoadAllRoutes(dir)
	if len(routes) != 0 {
		t.Errorf("expected 0 routes for empty dir, got %d", len(routes))
	}
}

func TestLoadAllRoutes_ReadsRouteMaps(t *testing.T) {
	dir := t.TempDir()
	rm := `{"inputs":[],"outputs":[],"routing":[{"from":"src.md","to":"dst.md"}]}`
	if err := os.WriteFile(filepath.Join(dir, "agent.route-map.json"), []byte(rm), 0o644); err != nil {
		t.Fatal(err)
	}

	routes := LoadAllRoutes(dir)
	if len(routes) != 1 {
		t.Fatalf("expected 1 route, got %d", len(routes))
	}
	if routes[0].From != "src.md" || routes[0].To != "dst.md" {
		t.Errorf("route fields wrong: %+v", routes[0])
	}
}

func TestLoadAllRoutes_MultipleFiles(t *testing.T) {
	dir := t.TempDir()
	rm := `{"routing":[{"from":"a.md","to":"b.md"},{"from":"c.md","to":"d.md"}]}`
	if err := os.WriteFile(filepath.Join(dir, "x.route-map.json"), []byte(rm), 0o644); err != nil {
		t.Fatal(err)
	}

	routes := LoadAllRoutes(dir)
	if len(routes) != 2 {
		t.Errorf("expected 2 routes, got %d", len(routes))
	}
}
