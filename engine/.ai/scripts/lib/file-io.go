package lib

import (
	"io"
	"log"
	"os"
	"path/filepath"
	"strings"
)

// RoutingResult describes the outcome of applying one routing rule.
type RoutingResult struct {
	From string
	To   string
	OK   bool
}

// LoadAllRoutes scans agentsDir recursively for *.route-map.json files and
// collects all routing rules from them.
func LoadAllRoutes(agentsDir string) []RoutingRule {
	var routes []RoutingRule
	_ = filepath.WalkDir(agentsDir, func(path string, d os.DirEntry, err error) error {
		if err != nil || d.IsDir() || !strings.HasSuffix(d.Name(), ".route-map.json") {
			return nil
		}
		rm, parseErr := LoadRouteMap(path)
		if parseErr != nil {
			log.Printf("file-io: %v", parseErr)
			return nil
		}
		routes = append(routes, rm.Routing...)
		return nil
	})
	return routes
}

// ApplyRouting copies files according to routing rules relative to projectRoot.
func ApplyRouting(rules []RoutingRule, projectRoot string) []RoutingResult {
	results := make([]RoutingResult, 0, len(rules))
	for _, rule := range rules {
		src := filepath.Join(projectRoot, rule.From)
		dst := filepath.Join(projectRoot, rule.To)
		results = append(results, RoutingResult{
			From: rule.From,
			To:   rule.To,
			OK:   copyAtomic(src, dst),
		})
	}
	return results
}

// WriteAtomic writes content to filePath atomically via a .tmp intermediary.
func WriteAtomic(filePath, content string) error {
	if err := os.MkdirAll(filepath.Dir(filePath), 0o755); err != nil {
		return err
	}
	tmp := filePath + ".tmp"
	if err := os.WriteFile(tmp, []byte(content), 0o644); err != nil {
		return err
	}
	return os.Rename(tmp, filePath)
}

func copyAtomic(src, dst string) bool {
	if _, err := os.Stat(src); err != nil {
		return false
	}
	if err := os.MkdirAll(filepath.Dir(dst), 0o755); err != nil {
		return false
	}
	in, err := os.Open(src)
	if err != nil {
		return false
	}
	defer in.Close()
	tmp := dst + ".tmp"
	out, err := os.Create(tmp)
	if err != nil {
		return false
	}
	if _, copyErr := io.Copy(out, in); copyErr != nil {
		out.Close()
		os.Remove(tmp)
		return false
	}
	out.Close()
	return os.Rename(tmp, dst) == nil
}
