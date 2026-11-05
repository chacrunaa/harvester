package repository

import (
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"
	"sync"
)

// mutexes guards per-file mutexes to prevent race conditions on read-modify-write.
var (
	mutexesMu sync.Mutex
	mutexes   = map[string]*sync.Mutex{}
)

func lockFor(path string) *sync.Mutex {
	mutexesMu.Lock()
	defer mutexesMu.Unlock()
	if m, ok := mutexes[path]; ok {
		return m
	}
	m := &sync.Mutex{}
	mutexes[path] = m
	return m
}

// ReadJSON reads and unmarshals a JSON file. Returns error if file doesn't exist.
func ReadJSON[T any](path string) (T, error) {
	var zero T
	data, err := os.ReadFile(path)
	if err != nil {
		return zero, err
	}
	var v T
	if err := json.Unmarshal(data, &v); err != nil {
		return zero, fmt.Errorf("unmarshal %s: %w", path, err)
	}
	return v, nil
}

// ReadJSONOr reads JSON file, returning fallback on any error.
func ReadJSONOr[T any](path string, fallback T) T {
	v, err := ReadJSON[T](path)
	if err != nil {
		return fallback
	}
	return v
}

// WriteJSONAtomic writes value to path atomically: .tmp → rename.
func WriteJSONAtomic(path string, v any) error {
	data, err := json.MarshalIndent(v, "", "  ")
	if err != nil {
		return fmt.Errorf("marshal: %w", err)
	}
	if err := os.MkdirAll(filepath.Dir(path), 0o755); err != nil {
		return err
	}
	tmp := path + ".tmp"
	if err := os.WriteFile(tmp, data, 0o644); err != nil {
		return err
	}
	return os.Rename(tmp, path)
}

// MutateJSON reads, modifies, and atomically writes a JSON file under a per-path mutex.
func MutateJSON[T any](path string, fn func(current *T) *T) (*T, error) {
	mu := lockFor(path)
	mu.Lock()
	defer mu.Unlock()

	current, err := ReadJSON[T](path)
	var ptr *T
	if err != nil {
		ptr = nil
	} else {
		ptr = &current
	}

	result := fn(ptr)
	if result == nil {
		return nil, nil
	}
	if err := WriteJSONAtomic(path, result); err != nil {
		return nil, err
	}
	return result, nil
}

// Exists reports whether path exists.
func Exists(path string) bool {
	_, err := os.Stat(path)
	return err == nil
}
