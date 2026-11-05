package ws

import (
	"github.com/gorilla/websocket"

	"harvester/backend/internal/service"
)

type wsClient struct {
	conn *websocket.Conn
	send chan []byte
	hub  *service.Hub
}

func (c *wsClient) Receive(data []byte) {
	select {
	case c.send <- data:
	default:
	}
}

func (c *wsClient) writePump() {
	defer func() {
		c.conn.Close()
		c.hub.Unsubscribe(c)
	}()
	for msg := range c.send {
		if err := c.conn.WriteMessage(websocket.TextMessage, msg); err != nil {
			return
		}
	}
}

func (c *wsClient) readPump() {
	defer func() {
		close(c.send)
		c.conn.Close()
		c.hub.Unsubscribe(c)
	}()
	for {
		if _, _, err := c.conn.ReadMessage(); err != nil {
			return
		}
	}
}
