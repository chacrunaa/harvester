import type { ChatId } from '../entity';

export type Agent = { id: string; title: string };

export const CHAT_AGENTS: Record<ChatId, Agent[]> = {
  analytics: [
    { id: 'product-manager', title: 'Product Manager' },
    { id: 'product-analyst', title: 'Product Analyst' },
    { id: 'market-analyst', title: 'Market Analyst' },
    { id: 'strategist', title: 'Strategist' },
    { id: 'financier', title: 'Financier' },
  ],
  systemic: [
    { id: 'owner', title: 'Owner' },
    { id: 'architect', title: 'Architect' },
    { id: 'analyst', title: 'Analyst' },
  ],
  development: [
    { id: 'dev-lead', title: 'Dev Lead' },
    { id: 'backend', title: 'Backend' },
    { id: 'frontend', title: 'Frontend' },
    { id: 'reviewers', title: 'Reviewers' },
  ],
  testing: [
    { id: 'qa-lead', title: 'QA Lead' },
    { id: 'qa', title: 'QA' },
    { id: 'penetration', title: 'Penetration Tester' },
  ],
};
