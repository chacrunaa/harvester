import { useEffect } from 'react';

import { useQuery } from '@tanstack/react-query';

import { fetchProjects } from '@/app/backend/projects';
import { useProjectStore } from '@/stores/project.store';

export const projectKeys = {
  all: ['projects'] as const,
  list: () => [...projectKeys.all, 'list'] as const,
};

export const useGetProjects = () => {
  const setProjects = useProjectStore((s) => s.setProjects);

  const query = useQuery({
    queryKey: projectKeys.list(),
    queryFn: fetchProjects,
  });

  useEffect(() => {
    if (query.data) setProjects(query.data);
  }, [query.data, setProjects]);

  return query;
};
