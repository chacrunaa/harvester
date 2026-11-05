export type ProviderId = 'claude' | 'codex' | 'deepseek' | 'gemini' | 'copilot' | 'kimi';

export type ProviderMeta = {
  id: ProviderId;
  name: string;
  description: string;
  color: string;
  initial: string;
};

export const PROVIDERS: ProviderMeta[] = [
  { id: 'claude',   name: 'Claude',   description: 'Anthropic',      color: '#e8622a', initial: 'C' },
  { id: 'codex',    name: 'Codex',    description: 'OpenAI',         color: '#10a37f', initial: 'O' },
  { id: 'deepseek', name: 'DeepSeek', description: 'DeepSeek AI',    color: '#2563eb', initial: 'D' },
  { id: 'gemini',   name: 'Gemini',   description: 'Google',         color: '#4285f4', initial: 'G' },
  { id: 'copilot',  name: 'Copilot',  description: 'GitHub / Azure', color: '#8250df', initial: 'P' },
  { id: 'kimi',     name: 'Kimi',     description: 'Moonshot AI',    color: '#00b96b', initial: 'K' },
];

export type SettingsDto = {
  provider: ProviderId;
  keyStatus: Record<ProviderId, boolean>;
};

export type UpdateSettingsPayload = {
  provider?: ProviderId;
  apiKey?: string;
};
