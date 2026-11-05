import type { ChatId, Message } from '@/modules/Chat/entity';

import { http } from './http';

export const CHAT_TO_PHASE: Record<ChatId, string> = {
  analytics: 'business',
  systemic: 'systemic',
  development: 'development',
  testing: 'testing',
};

export const PHASE_TO_CHAT_ID: Record<string, ChatId> = {
  business: 'analytics',
  systemic: 'systemic',
  development: 'development',
  testing: 'testing',
};

type BackendMsg = {
  id?: string;
  type: string;
  agent?: string;
  content: string;
  timestamp?: string;
};

function mapMsg(msg: BackendMsg, chatId: ChatId, phase: string): Message {
  const id = msg.id ?? `msg-${msg.timestamp ?? Date.now()}`;
  const createdAt = msg.timestamp ?? new Date().toISOString();
  if (msg.type === 'agent') {
    return {
      id,
      chatId,
      type: 'agent-card',
      content: {
        agentId: `${phase}/${msg.agent ?? 'agent'}`,
        agentTitle: msg.agent ?? 'Агент',
        summary: msg.content,
      },
      createdAt,
    };
  }
  return { id, chatId, type: 'user', content: msg.content, createdAt };
}

export async function fetchChatMessages(chatId: ChatId): Promise<Message[]> {
  const phase = CHAT_TO_PHASE[chatId];
  const raw = await http.get<BackendMsg[]>(`/api/chats/${phase}`);
  return raw.map((msg) => mapMsg(msg, chatId, phase));
}

export async function postChatMessage(
  chatId: ChatId,
  content: string,
  mentions: string[] = [],
): Promise<Message> {
  const phase = CHAT_TO_PHASE[chatId];
  const raw = await http.post<BackendMsg>(`/api/chats/${phase}`, {
    content,
    type: 'user',
    mentions,
  });
  return mapMsg({ ...raw, type: 'user' }, chatId, phase);
}
