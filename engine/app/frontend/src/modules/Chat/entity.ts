export type ChatId = 'analytics' | 'systemic' | 'development' | 'testing';

export type MessageType = 'system' | 'user' | 'agent-card' | 'qna-form';

export type SystemMessageContent = string;
export type UserMessageContent = string;

export type AgentCardContent = {
  agentId: string;
  agentTitle: string;
  summary: string;
};

export type QnaQuestion = {
  id: string;
  text: string;
  answer: string | null;
};

export type QnaFormContent = {
  agentId: string;
  questions: QnaQuestion[];
};

export type Message =
  | { id: string; chatId: ChatId; type: 'system'; content: SystemMessageContent; createdAt: string }
  | { id: string; chatId: ChatId; type: 'user'; content: UserMessageContent; createdAt: string }
  | { id: string; chatId: ChatId; type: 'agent-card'; content: AgentCardContent; createdAt: string }
  | { id: string; chatId: ChatId; type: 'qna-form'; content: QnaFormContent; createdAt: string };

export type MessageProps<T extends Message = Message> = {
  message: T;
};
