import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';

import { fetchChatMessages, postChatMessage } from '@/app/backend/chats';

import type { ChatId, Message } from './entity';

export const chatKeys = {
  all: ['chat'] as const,
  details: () => [...chatKeys.all, 'detail'] as const,
  detail: (projectId: string, chatId: ChatId) =>
    [...chatKeys.details(), projectId, chatId] as const,
  messages: (projectId: string, chatId: ChatId) =>
    [...chatKeys.detail(projectId, chatId), 'messages'] as const,
};

export const useChatMessages = (projectId: string | null, chatId: ChatId | null) =>
  useQuery({
    queryKey: projectId && chatId ? chatKeys.messages(projectId, chatId) : ['chat', 'idle'],
    queryFn: () => {
      if (!projectId || !chatId) return Promise.resolve<Message[]>([]);
      return fetchChatMessages(chatId);
    },
    enabled: !!projectId && !!chatId,
  });

type SendPayload = { content: string; mentions: string[] };

export const useSendMessage = (projectId: string | null, chatId: ChatId | null) => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ content, mentions }: SendPayload) => {
      if (!projectId || !chatId) {
        return Promise.reject(new Error('No active project or chat'));
      }
      return postChatMessage(chatId, content, mentions);
    },
    onMutate: async ({ content }: SendPayload) => {
      if (!projectId || !chatId) return;
      const qk = chatKeys.messages(projectId, chatId);
      await queryClient.cancelQueries({ queryKey: qk });
      const previous = queryClient.getQueryData<Message[]>(qk);
      const optimistic: Message = {
        id: `opt-${Date.now()}`,
        chatId,
        type: 'user',
        content,
        createdAt: new Date().toISOString(),
      };
      queryClient.setQueryData<Message[]>(qk, (old) => [...(old ?? []), optimistic]);
      return { previous, optimisticId: optimistic.id };
    },
    onSuccess: (newMessage, _, ctx) => {
      if (!projectId || !chatId || !ctx) return;
      const qk = chatKeys.messages(projectId, chatId);
      queryClient.setQueryData<Message[]>(qk, (old) =>
        (old ?? []).map((m) => (m.id === ctx.optimisticId ? newMessage : m)),
      );
    },
    onError: (_, __, ctx) => {
      if (!projectId || !chatId || !ctx) return;
      queryClient.setQueryData(chatKeys.messages(projectId, chatId), ctx.previous);
    },
  });
};
