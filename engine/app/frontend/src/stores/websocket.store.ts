import { create } from 'zustand';

export type WebsocketStatus = 'connecting' | 'connected' | 'disconnected' | 'error';

type WebsocketState = {
  status: WebsocketStatus;
  lastError: string | null;
  setStatus: (status: WebsocketStatus) => void;
  setError: (message: string | null) => void;
};

export const useWebsocketStore = create<WebsocketState>((set) => ({
  status: 'disconnected',
  lastError: null,
  setStatus: (status) => set({ status }),
  setError: (lastError) => set({ lastError }),
}));
