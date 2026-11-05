import type { ChatId } from '../entity';

export const CHAT_IDS: readonly ChatId[] = ['analytics', 'systemic', 'development', 'testing'] as const;

export const CHAT_TITLES: Record<ChatId, string> = {
  analytics: 'Аналитика',
  systemic: 'Системная аналитика',
  development: 'Разработка',
  testing: 'Тестирование',
};
