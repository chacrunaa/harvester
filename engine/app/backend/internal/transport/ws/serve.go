package ws

import (
	"log"
	"net/http"

	"github.com/gorilla/websocket"

	"harvester/backend/internal/service"
)

var upgrader = websocket.Upgrader{
	CheckOrigin: func(r *http.Request) bool { return true },
}

func ServeWS(h *service.Hub, w http.ResponseWriter, r *http.Request) {
	conn, err := upgrader.Upgrade(w, r, nil)
	if err != nil {
		log.Printf("ws: upgrade error: %v", err)
		return
	}
	c := &wsClient{conn: conn, send: make(chan []byte, 64), hub: h}
	h.Subscribe(c)
	go c.writePump()
	go c.readPump()
}
