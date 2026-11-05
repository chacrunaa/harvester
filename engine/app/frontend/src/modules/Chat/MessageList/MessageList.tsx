import { InitFlow } from '@/modules/InitFlow';
import { useProjectStore } from '@/stores/project.store';
import { useWorkspaceStore } from '@/stores/workspace.store';

import type { Message } from '../entity';
import { useChatMessages } from '../query';
import { messageRendererRegistry } from '../services';

import styles from './MessageList.module.scss';

export const MessageList = () => {
  const project = useProjectStore((s) => s.getSelectedProject());
  const activeChatId = useWorkspaceStore((s) => s.activeChatId);

  const { data: messages = [], isPending } = useChatMessages(project?.id ?? null, activeChatId);

  if (!project) {
    return <div className={styles.empty}>Выберите проект</div>;
  }

  if (!project.isInitialized) {
    return <InitFlow />;
  }

  if (!activeChatId) {
    return <div className={styles.empty}>Выберите вкладку чата</div>;
  }

  if (isPending) {
    return <div className={styles.empty}>Загрузка…</div>;
  }

  return (
    <div className={styles.root}>
      {messages.map((message: Message) => {
        const Renderer = messageRendererRegistry[message.type];
        return <Renderer key={message.id} message={message} />;
      })}
    </div>
  );
};
