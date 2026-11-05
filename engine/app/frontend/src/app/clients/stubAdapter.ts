import type { ChatId, Message } from '@/modules/Chat/entity';
import type { Project } from '@/types/project';

export type ProjectSnapshot = {
  projectId: string;
  isInitialized: boolean;
  currentTaskId: string | null;
  taskNumber: number | null;
  enabledChats: ChatId[];
  messages: Record<ChatId, Message[]>;
};

const STUBS_BASE = '/stubs';

const fetchJson = async <T,>(url: string): Promise<T> => {
  const response = await fetch(url);
  if (!response.ok) throw new Error(`Stub fetch failed: ${url} (${response.status})`);
  return (await response.json()) as T;
};

export const stubAdapter = {
  fetchProjects: (): Promise<Project[]> => fetchJson<Project[]>(`${STUBS_BASE}/projects.json`),

  fetchProjectSnapshot: (projectId: string): Promise<ProjectSnapshot> =>
    fetchJson<ProjectSnapshot>(`${STUBS_BASE}/projects/${projectId}.json`),

  fetchMessages: async (projectId: string, chatId: ChatId): Promise<Message[]> => {
    const snapshot = await stubAdapter.fetchProjectSnapshot(projectId);
    return snapshot.messages[chatId] ?? [];
  },

  sendMessage: (projectId: string, chatId: ChatId, text: string): Promise<Message> => {
    const message: Message = {
      id: `local-${Date.now()}`,
      chatId,
      type: 'user',
      content: text,
      createdAt: new Date().toISOString(),
    };
    void projectId;
    return Promise.resolve(message);
  },
} as const;
