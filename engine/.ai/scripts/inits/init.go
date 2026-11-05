package inits

import (
	"encoding/json"
	"fmt"
	"io"
	"os"
	"path/filepath"
	"time"
)

// Init creates a .ai/ directory structure for a new project by copying the
// harvester skeleton template and stamping the pipeline-state.json with taskID.
//
//   - taskID       — e.g. "TF-001"
//   - projectDir   — absolute path where .ai/ will be created
//   - harvesterRoot — absolute path to the harvester repo root (contains templates/ai/)
func Init(taskID, projectDir, harvesterRoot string) error {
	skeleton := filepath.Join(harvesterRoot, "templates", "ai")
	target := filepath.Join(projectDir, ".ai")

	if _, err := os.Stat(target); err == nil {
		return fmt.Errorf(".ai/ already exists at %s", target)
	}
	if _, err := os.Stat(skeleton); err != nil {
		return fmt.Errorf("skeleton not found: %s", skeleton)
	}

	if err := copyDir(skeleton, target); err != nil {
		return fmt.Errorf("copy skeleton: %w", err)
	}

	stateFile := filepath.Join(target, "pipeline-state.json")
	if err := stampState(stateFile, taskID); err != nil {
		return fmt.Errorf("update pipeline-state.json: %w", err)
	}

	return nil
}

// stampState writes task_id and created_at into a pipeline-state.json
// copied from the template (where those fields are empty strings).
func stampState(path, taskID string) error {
	data, err := os.ReadFile(path)
	if err != nil {
		return err
	}
	var state map[string]interface{}
	if err := json.Unmarshal(data, &state); err != nil {
		return fmt.Errorf("parse %s: %w", path, err)
	}
	state["task_id"] = taskID
	state["created_at"] = time.Now().UTC().Format(time.RFC3339)

	out, err := json.MarshalIndent(state, "", "  ")
	if err != nil {
		return err
	}
	tmp := path + ".tmp"
	if err := os.WriteFile(tmp, out, 0o644); err != nil {
		return err
	}
	return os.Rename(tmp, path)
}

func copyDir(src, dst string) error {
	return filepath.WalkDir(src, func(path string, d os.DirEntry, err error) error {
		if err != nil {
			return err
		}
		rel, _ := filepath.Rel(src, path)
		dstPath := filepath.Join(dst, rel)
		if d.IsDir() {
			return os.MkdirAll(dstPath, 0o755)
		}
		return copyFile(path, dstPath)
	})
}

func copyFile(src, dst string) error {
	in, err := os.Open(src)
	if err != nil {
		return err
	}
	defer in.Close()

	if err := os.MkdirAll(filepath.Dir(dst), 0o755); err != nil {
		return err
	}
	tmp := dst + ".tmp"
	out, err := os.Create(tmp)
	if err != nil {
		return err
	}
	if _, err := io.Copy(out, in); err != nil {
		out.Close()
		os.Remove(tmp)
		return err
	}
	out.Close()
	return os.Rename(tmp, dst)
}
