package lib

import (
	"fmt"
	"log"
	"os"
	"path/filepath"
	"strings"
)

type docsMapping struct {
	source       string
	docs         string
	title        string
	instructions []string
}

var docsMap = map[string]docsMapping{
	"business/product-manager": {
		source:       "chats/business/brief-business.md",
		docs:         "docs/{task-id}/business/brief.md",
		title:        "Бизнес-бриф продукта",
		instructions: []string{"01-product-brief.md", "11-mvp-definition.md"},
	},
	"business/product-analyst": {
		source:       "chats/business/product-analyst/report.md",
		docs:         "docs/{task-id}/business/product-analyst.md",
		title:        "Продуктовый анализ: ЦА, ценность, метрики",
		instructions: []string{"02-target-audience.md", "07-value-proposition.md", "09-product-metrics.md", "12-custdev-plan.md"},
	},
	"business/market-analyst": {
		source:       "chats/business/market-analyst/report.md",
		docs:         "docs/{task-id}/business/market-analyst.md",
		title:        "Анализ рынка: конкуренты, объём, инсайты",
		instructions: []string{"03-competitive-analysis.md", "05-market-size.md", "13-market-insights.md"},
	},
	"business/strategist": {
		source:       "chats/business/strategist/report.md",
		docs:         "docs/{task-id}/business/strategist.md",
		title:        "Стратегия и бизнес-модель",
		instructions: []string{"06-business-model.md", "07-value-proposition.md"},
	},
	"business/financier": {
		source:       "chats/business/financier/report.md",
		docs:         "docs/{task-id}/business/financier.md",
		title:        "Финансовый анализ: юнит-экономика и модель",
		instructions: []string{"08-unit-economics.md", "10-financial-model.md"},
	},
	"systemic/owner": {
		source:       "chats/systemic/owner/spec.md",
		docs:         "docs/{task-id}/systemic/spec.md",
		title:        "Системная спецификация и функциональные требования",
		instructions: []string{"04-bft.md"},
	},
	"systemic/architect": {
		source:       "chats/systemic/architect/tech-proposal.md",
		docs:         "docs/{task-id}/systemic/architecture.md",
		title:        "Архитектура системы",
		instructions: []string{"15-architecture.md"},
	},
	"systemic/analyst": {
		source:       "chats/systemic/analyst/spec.md",
		docs:         "docs/{task-id}/systemic/api-spec.md",
		title:        "API и модель данных",
		instructions: []string{"16-api-spec.md"},
	},
	"development/backend": {
		source:       "chats/development/backend/report.md",
		docs:         "docs/{task-id}/development/backend.md",
		title:        "Backend: что реализовано",
		instructions: []string{"17-backend.md"},
	},
	"development/frontend": {
		source:       "chats/development/frontend/report.md",
		docs:         "docs/{task-id}/development/frontend.md",
		title:        "Frontend: что реализовано",
		instructions: []string{"18-frontend.md"},
	},
	"development/reviewers": {
		source:       "chats/development/reviewers/review.md",
		docs:         "docs/{task-id}/development/review.md",
		title:        "Ревью кода",
		instructions: []string{"19-code-review.md"},
	},
	"testing/qa": {
		source:       "chats/testing/qa/report.md",
		docs:         "docs/{task-id}/testing/qa.md",
		title:        "Результаты тестирования",
		instructions: []string{"20-qa-testing.md"},
	},
	"testing/penetration": {
		source:       "chats/testing/penetration/report.md",
		docs:         "docs/{task-id}/testing/security.md",
		title:        "Анализ безопасности",
		instructions: []string{"21-security.md"},
	},
}

const baseDocsPrompt = `Ты — технический писатель, который создаёт понятную бизнес-документацию на основе отчётов AI-агентов.

Твоя задача: написать ОТДЕЛЬНЫЙ, САМОДОСТАТОЧНЫЙ документ для начинающего бизнес-аналитика или разработчика. Документ должен быть понятен человеку без специальных знаний.

ОБЯЗАТЕЛЬНЫЕ правила:
1. Пиши простым русским языком — без жаргона.
2. Будь подробным — расписывай каждый пункт полностью, не сокращай.
3. Не копируй технический текст дословно — перефразируй и объясняй своими словами.
4. Добавляй раздел "💡 Почему это важно" там, где объясняешь ключевые концепции.
5. Структурируй через заголовки H2/H3 и маркированные списки.
6. В конце ОБЯЗАТЕЛЬНО добавь раздел "## Ключевые выводы" — 3-5 пунктов самого важного.
7. Тон: дружелюбный, наставнический.
8. Начинай сразу с содержания, без вводных фраз типа "Вот документ".`

// WriteDocs generates a beginner-friendly docs file for an agent's output.
// Designed to be called asynchronously: go lib.WriteDocs(...)
func WriteDocs(agentID, taskID, aiDir, projectRoot, logDir string, lc Config, harvestAiDir string) {
	m, ok := docsMap[agentID]
	if !ok {
		return
	}
	sourceData, err := os.ReadFile(filepath.Join(aiDir, m.source))
	if err != nil || len(strings.TrimSpace(string(sourceData))) == 0 {
		return
	}

	systemPrompt := buildDocsSystemPrompt(m, harvestAiDir)
	userPrompt := fmt.Sprintf(
		"Агент: %s\nДокумент: %s\ntask-id: %s\n\n---\n\nИСХОДНЫЙ ТЕХНИЧЕСКИЙ ОТЧЁТ:\n\n%s",
		agentID, m.title, strOr(taskID, "—"), string(sourceData),
	)

	// Call is in the same package (llm-client.go)
	content, err := Call(lc, systemPrompt, userPrompt, CallOpts{
		Agent:  "docs-writer/" + agentID,
		TaskID: taskID,
		LogDir: logDir,
	})
	if err != nil {
		log.Printf("[docs-writer] %s: LLM call failed: %v", agentID, err)
		return
	}

	docsRelPath := strings.ReplaceAll(m.docs, "{task-id}", strOr(taskID, "unknown"))
	docsAbsPath := filepath.Join(projectRoot, docsRelPath)
	if err := os.MkdirAll(filepath.Dir(docsAbsPath), 0o755); err != nil {
		return
	}
	tmp := docsAbsPath + ".tmp"
	if err := os.WriteFile(tmp, []byte(content), 0o644); err != nil {
		return
	}
	if err := os.Rename(tmp, docsAbsPath); err != nil {
		return
	}
	log.Printf("[docs-writer] %s: wrote %s", agentID, docsRelPath)
}

func buildDocsSystemPrompt(m docsMapping, harvestAiDir string) string {
	rulesDir := filepath.Join(harvestAiDir, "rules", "docs")
	var instructions []string
	for _, f := range m.instructions {
		data, err := os.ReadFile(filepath.Join(rulesDir, f))
		if err != nil {
			continue
		}
		instructions = append(instructions, string(data))
	}
	if len(instructions) == 0 {
		return baseDocsPrompt
	}
	var sb strings.Builder
	sb.WriteString(baseDocsPrompt)
	sb.WriteString("\n\n---\n\n## Методологические инструкции\n\n")
	for i, inst := range instructions {
		fmt.Fprintf(&sb, "### Инструкция %d\n\n%s\n\n---\n\n", i+1, inst)
	}
	return sb.String()
}

func strOr(s, fallback string) string {
	if s != "" {
		return s
	}
	return fallback
}
