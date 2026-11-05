import type { Project } from '@/types/project';

import { http } from './http';

type BackendProject = {
  id: string;
  label: string;
  aiDir: string;
  active: boolean;
};

export async function fetchProjects(): Promise<Project[]> {
  const raw = await http.get<BackendProject[]>('/api/projects');
  return raw.map((p) => ({
    id: p.id,
    name: p.label,
    path: p.aiDir,
    isInitialized: true,
  }));
}
