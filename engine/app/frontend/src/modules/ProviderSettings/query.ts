import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';

import { getSettings, updateSettings } from '@/app/backend';

import type { SettingsDto, UpdateSettingsPayload } from './entity';

export const settingsKeys = {
  all: ['settings'] as const,
};

export function useGetSettings() {
  return useQuery<SettingsDto>({
    queryKey: settingsKeys.all,
    queryFn: getSettings,
  });
}

export function useUpdateSettings() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (payload: UpdateSettingsPayload) => updateSettings(payload),
    onSuccess: () => qc.invalidateQueries({ queryKey: settingsKeys.all }),
  });
}
