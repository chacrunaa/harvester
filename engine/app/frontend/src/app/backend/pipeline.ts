import type { ChatId } from '@/modules/Chat/entity';

import { http } from './http';

const PHASE_ORDER = ['business', 'systemic', 'development', 'testing'] as const;

type Phase = (typeof PHASE_ORDER)[number];

// Ключи — литеральное объединение фаз, а не string: тогда доступ по
// индексу тотален и не даёт ChatId | undefined.
const PHASE_TO_CHAT_ID: Record<Phase, ChatId> = {
  business: 'analytics',
  systemic: 'systemic',
  development: 'development',
  testing: 'testing',
};

const ALL_CHATS: ChatId[] = ['analytics', 'systemic', 'development', 'testing'];

type PipelineState = { 'task-id'?: string; phase?: string };

export type PipelineSnapshot = {
  projectId: string;
  isInitialized: boolean;
  currentTaskId: string | null;
  taskNumber: number | null;
  enabledChats: ChatId[];
};

export async function fetchPipelineSnapshot(projectId: string): Promise<PipelineSnapshot> {
  let enabledChats: ChatId[] = ALL_CHATS;
  let currentTaskId: string | null = null;

  const state = await http.get<PipelineState | null>('/api/pipeline/state').catch(() => null);
  if (state) {
    currentTaskId = state['task-id'] ?? null;
    const idx = PHASE_ORDER.indexOf(state.phase as Phase);
    if (idx >= 0) {
      enabledChats = PHASE_ORDER.slice(0, idx + 1).map((p) => PHASE_TO_CHAT_ID[p]);
    }
  }

  return { projectId, isInitialized: true, currentTaskId, taskNumber: null, enabledChats };
}
