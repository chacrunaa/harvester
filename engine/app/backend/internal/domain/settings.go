package domain

type SettingsSnapshot struct {
	Provider  string          `json:"provider"`
	KeyStatus map[string]bool `json:"keyStatus"`
}
