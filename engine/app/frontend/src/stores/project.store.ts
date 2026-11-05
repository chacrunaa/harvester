import { create } from 'zustand';

import type { Project } from '@/types/project';

type ProjectStore = {
  projects: Project[];
  selectedProjectId: string | null;
  setProjects: (projects: Project[]) => void;
  setSelectedProject: (id: string) => void;
  getSelectedProject: () => Project | null;
};

export const useProjectStore = create<ProjectStore>((set, get) => ({
  projects: [],
  selectedProjectId: null,
  setProjects: (projects) => set({ projects }),
  setSelectedProject: (id) => set({ selectedProjectId: id }),
  getSelectedProject: () => {
    const { projects, selectedProjectId } = get();
    if (!selectedProjectId) return null;
    return projects.find((p) => p.id === selectedProjectId) ?? null;
  },
}));
