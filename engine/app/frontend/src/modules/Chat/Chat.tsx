import { useEffect } from 'react';

import { useQuery } from '@tanstack/react-query';

import { fetchPipelineSnapshot } from '@/app/backend/pipeline';
import { useProjectStore } from '@/stores/project.store';
import { useWorkspaceStore } from '@/stores/workspace.store';

import { ChatTabs } from './ChatTabs/ChatTabs';
import { useChatSocket } from './hooks/useChatSocket';
import { MessageInput } from './MessageInput/MessageInput';
import { MessageList } from './MessageList/MessageList';

import styles from './Chat.module.scss';

const snapshotKey = (projectId: string) => ['project', projectId, 'snapshot'] as const;

export const Chat = () => {
  const projectId = useProjectStore((s) => s.selectedProjectId);
  const setEnabledChats = useWorkspaceStore((s) => s.setEnabledChats);
  const setActiveChatId = useWorkspaceStore((s) => s.setActiveChatId);
  const setCurrentTask = useWorkspaceStore((s) => s.setCurrentTask);
  const resetWorkspace = useWorkspaceStore((s) => s.resetWorkspace);

  const { data: snapshot } = useQuery({
    queryKey: projectId ? snapshotKey(projectId) : ['project', 'idle', 'snapshot'],
    queryFn: () => {
      if (!projectId) throw new Error('no projectId');
      return fetchPipelineSnapshot(projectId);
    },
    enabled: !!projectId,
  });

  useEffect(() => {
    if (!snapshot) {
      resetWorkspace();
      return;
    }
    setEnabledChats(snapshot.enabledChats);
    setCurrentTask(snapshot.currentTaskId, snapshot.taskNumber);
    const firstEnabled = snapshot.enabledChats[0];
    if (firstEnabled) setActiveChatId(firstEnabled);
  }, [snapshot, setEnabledChats, setActiveChatId, setCurrentTask, resetWorkspace]);

  useChatSocket(projectId);

  return (
    <div className={styles.root}>
      <ChatTabs />
      <div className={styles.body}>
        <MessageList />
      </div>
      <MessageInput />
    </div>
  );
};
