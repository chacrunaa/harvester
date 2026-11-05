package service

import (
	"encoding/json"
	"log"
	"sync"
)

// Hub broadcasts events to all subscribed clients.
type Hub struct {
	mu          sync.RWMutex
	subscribers map[Subscriber]struct{}
}

func NewHub() *Hub {
	return &Hub{subscribers: make(map[Subscriber]struct{})}
}

func (h *Hub) Subscribe(s Subscriber) {
	h.mu.Lock()
	h.subscribers[s] = struct{}{}
	h.mu.Unlock()
}

func (h *Hub) Unsubscribe(s Subscriber) {
	h.mu.Lock()
	delete(h.subscribers, s)
	h.mu.Unlock()
}

func (h *Hub) Broadcast(eventType string, payload any) {
	data, err := json.Marshal(struct {
		Type    string `json:"type"`
		Payload any    `json:"payload"`
	}{Type: eventType, Payload: payload})
	if err != nil {
		log.Printf("hub: marshal error: %v", err)
		return
	}
	h.mu.RLock()
	defer h.mu.RUnlock()
	for s := range h.subscribers {
		s.Receive(data)
	}
}
