import { PHASE_TO_CHAT_ID } from '@/app/backend/chats';
import { useWebsocketStore } from '@/stores/websocket.store';

export type WsEvent = { type: string; [key: string]: unknown };
export type WsHandler = (event: WsEvent) => void;
export type WsUnsubscribe = () => void;

type AgentMessagePayload = {
  phase: string;
  message: { type?: string; agent?: string; content?: string; timestamp?: string };
};

const isTauri = typeof window !== 'undefined' && '__TAURI__' in window;

const setStatus = useWebsocketStore.getState().setStatus;

const handlers = new Map<string, Set<WsHandler>>();
let ws: WebSocket | null = null;

function dispatch(type: string, payload: Record<string, unknown>): void {
  const bucket = handlers.get(type);
  if (!bucket) return;
  for (const h of bucket) h({ type, ...payload });
}

function handleAgentMessage(data: AgentMessagePayload): void {
  if (data.message?.type !== 'agent') return;
  const chatId = PHASE_TO_CHAT_ID[data.phase];
  if (!chatId) return;
  dispatch('chat_message', {
    id: `ws-${data.message.timestamp ?? Date.now()}`,
    chatId,
    messageType: 'agent-card',
    content: {
      agentId: `${data.phase}/${data.message.agent ?? 'agent'}`,
      agentTitle: data.message.agent ?? 'Агент',
      summary: data.message.content ?? '',
    },
    createdAt: data.message.timestamp ?? new Date().toISOString(),
  });
}

// ── Tauri mode ────────────────────────────────────────────────────────────────

let tauriUnlisteners: Map<string, Promise<() => void>> | null = null;

async function ensureTauriListeners(type: string): Promise<void> {
  const { listen } = await import('@tauri-apps/api/event');
  if (!tauriUnlisteners) tauriUnlisteners = new Map();

  const eventName = type === 'chat_message' ? 'agent:message' : type;
  if (tauriUnlisteners.has(eventName)) return;

  const promise = listen<unknown>(eventName, (event) => {
    const payload = (event.payload ?? {}) as Record<string, unknown>;
    if (eventName === 'agent:message') {
      handleAgentMessage(payload as AgentMessagePayload);
      return;
    }
    dispatch(eventName, payload);
  });
  tauriUnlisteners.set(eventName, promise as Promise<() => void>);
}

// ── WebSocket mode ────────────────────────────────────────────────────────────

// In dev mode Vite proxy forwards /ws → backend, so same-host URL works.
// In production builds use VITE_WS_URL if set, otherwise assume same-host /ws.
const WS_URL = (() => {
  if (import.meta.env.VITE_WS_URL) return import.meta.env.VITE_WS_URL as string;
  if (typeof window === 'undefined') return 'ws://127.0.0.1:3100/ws';
  const proto = window.location.protocol === 'https:' ? 'wss' : 'ws';
  return `${proto}://${window.location.host}/ws`;
})();

function connectWebSocket(): void {
  if (ws && ws.readyState < WebSocket.CLOSING) return;

  ws = new WebSocket(WS_URL);

  ws.onopen = () => setStatus('connected');

  ws.onmessage = (event) => {
    let msg: { type?: string; payload?: Record<string, unknown> };
    try {
      msg = JSON.parse(event.data as string) as typeof msg;
    } catch {
      return;
    }
    const { type, payload = {} } = msg;
    if (!type) return;
    if (type === 'agent:message') {
      handleAgentMessage(payload as AgentMessagePayload);
    }
    dispatch(type, payload);
  };

  ws.onerror = () => setStatus('error' as Parameters<typeof setStatus>[0]);

  ws.onclose = () => {
    setStatus('disconnected');
    setTimeout(connectWebSocket, 3000);
  };
}

// ── Public API ────────────────────────────────────────────────────────────────

export const websocketClient = {
  connect: (): void => {
    if (isTauri) {
      setStatus('connected');
    } else {
      connectWebSocket();
    }
  },

  disconnect: (): void => {
    if (isTauri && tauriUnlisteners) {
      for (const p of tauriUnlisteners.values()) {
        void p.then((unlisten) => unlisten());
      }
      tauriUnlisteners.clear();
    } else if (ws) {
      ws.onclose = null;
      ws.close();
      ws = null;
    }
    setStatus('disconnected');
  },

  send: (_message: unknown): void => {
    // Tauri mode: use invoke(); web mode: sends not needed (server pushes via hub)
  },

  subscribe: (type: string, handler: WsHandler): WsUnsubscribe => {
    let bucket = handlers.get(type);
    if (!bucket) {
      bucket = new Set<WsHandler>();
      handlers.set(type, bucket);
    }
    bucket.add(handler);

    if (isTauri) {
      void ensureTauriListeners(type);
    }

    return () => {
      bucket?.delete(handler);
    };
  },
};
