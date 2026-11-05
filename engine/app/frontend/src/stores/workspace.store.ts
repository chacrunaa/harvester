import { create } from 'zustand';

import type { ChatId } from '@/modules/Chat/entity';

type WorkspaceStore = {
  activeChatId: ChatId | null;
  enabledChats: Set<ChatId>;
  currentTaskId: string | null;
  taskNumber: number | null;
  setActiveChatId: (chatId: ChatId) => void;
  setEnabledChats: (chats: ChatId[]) => void;
  setCurrentTask: (taskId: string | null, taskNumber: number | null) => void;
  resetWorkspace: () => void;
};

const INITIAL_STATE = {
  activeChatId: null as ChatId | null,
  enabledChats: new Set<ChatId>(),
  currentTaskId: null as string | null,
  taskNumber: null as number | null,
};

export const useWorkspaceStore = create<WorkspaceStore>((set) => ({
  ...INITIAL_STATE,
  setActiveChatId: (chatId) => set({ activeChatId: chatId }),
  setEnabledChats: (chats) => set({ enabledChats: new Set(chats) }),
  setCurrentTask: (taskId, taskNumber) => set({ currentTaskId: taskId, taskNumber }),
  resetWorkspace: () => set({ ...INITIAL_STATE, enabledChats: new Set<ChatId>() }),
}));
