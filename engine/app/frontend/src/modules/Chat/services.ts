import type { ComponentType } from 'react';

import type { WsEvent } from '@/app/clients/websocketClient';

import { AgentCard } from './MessageList/renderers/AgentCard';
import { QnaForm } from './MessageList/renderers/QnaForm';
import { SystemMessage } from './MessageList/renderers/SystemMessage';
import { UserMessage } from './MessageList/renderers/UserMessage';
import type { Message, MessageProps, MessageType } from './entity';

export const messageRendererRegistry: Record<MessageType, ComponentType<MessageProps>> = {
  system: SystemMessage as ComponentType<MessageProps>,
  user: UserMessage as ComponentType<MessageProps>,
  'agent-card': AgentCard as ComponentType<MessageProps>,
  'qna-form': QnaForm as ComponentType<MessageProps>,
};

export const mapWsEventToMessage = (event: WsEvent): Message | null => {
  if (typeof event.id !== 'string' || typeof event.chatId !== 'string') return null;
  const type = event.messageType;
  if (type !== 'system' && type !== 'user' && type !== 'agent-card' && type !== 'qna-form') {
    return null;
  }
  return {
    id: event.id,
    chatId: event.chatId as Message['chatId'],
    type,
    content: event.content,
    createdAt: typeof event.createdAt === 'string' ? event.createdAt : new Date().toISOString(),
  } as Message;
};
