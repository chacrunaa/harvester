import { useEffect } from 'react';

import { useQueryClient } from '@tanstack/react-query';

import { websocketClient } from '@/app/clients/websocketClient';
import { useWorkspaceStore } from '@/stores/workspace.store';

import type { Message } from '../entity';
import { chatKeys } from '../query';
import { mapWsEventToMessage } from '../services';

export const useChatSocket = (projectId: string | null) => {
  const queryClient = useQueryClient();
  const activeChatId = useWorkspaceStore((s) => s.activeChatId);

  useEffect(() => {
    if (!projectId || !activeChatId) return;

    const off = websocketClient.subscribe('chat_message', (event) => {
      if (event.chatId !== activeChatId) return;
      const message = mapWsEventToMessage(event);
      if (!message) return;
      queryClient.setQueryData<Message[]>(
        chatKeys.messages(projectId, activeChatId),
        (prev = []) => [...prev, message],
      );
    });

    return off;
  }, [projectId, activeChatId, queryClient]);
};
