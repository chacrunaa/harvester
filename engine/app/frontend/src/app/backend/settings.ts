import { invoke } from '@tauri-apps/api/core';

import type { SettingsDto, UpdateSettingsPayload } from '@/modules/ProviderSettings/entity';

import { http } from './http';

export async function getSettings(): Promise<SettingsDto> {
  return http.get('/api/settings');
}

export async function updateSettings(payload: UpdateSettingsPayload): Promise<SettingsDto> {
  // Persist to Rust SQLite so the key survives restarts (via settings:loaded handshake)
  await invoke('update_settings', {
    provider: payload.provider ?? null,
    apiKey: payload.apiKey ?? null,
  });
  return http.post('/api/settings', payload);
}
