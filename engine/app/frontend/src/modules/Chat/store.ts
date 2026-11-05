import { create } from 'zustand';

import type { ChatId } from './entity';

type ChatStore = {
  inputDraft: Partial<Record<ChatId, string>>;
  scrollPosition: Partial<Record<ChatId, number>>;
  setInputDraft: (chatId: ChatId, value: string) => void;
  setScrollPosition: (chatId: ChatId, position: number) => void;
};

export const useChatStore = create<ChatStore>((set) => ({
  inputDraft: {},
  scrollPosition: {},
  setInputDraft: (chatId, value) =>
    set((state) => ({ inputDraft: { ...state.inputDraft, [chatId]: value } })),
  setScrollPosition: (chatId, position) =>
    set((state) => ({ scrollPosition: { ...state.scrollPosition, [chatId]: position } })),
}));
