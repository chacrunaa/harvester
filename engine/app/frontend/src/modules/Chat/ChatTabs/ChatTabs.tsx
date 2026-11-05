import { useWorkspaceStore } from '@/stores/workspace.store';

import { CHAT_IDS, CHAT_TITLES } from '../constants/chatIds';

import styles from './ChatTabs.module.scss';

export const ChatTabs = () => {
  const activeChatId = useWorkspaceStore((s) => s.activeChatId);
  const enabledChats = useWorkspaceStore((s) => s.enabledChats);
  const setActiveChatId = useWorkspaceStore((s) => s.setActiveChatId);

  return (
    <div className={styles.root} role="tablist">
      {CHAT_IDS.map((chatId) => {
        const isEnabled = enabledChats.has(chatId);
        const isActive = chatId === activeChatId;
        return (
          <button
            key={chatId}
            type="button"
            role="tab"
            aria-selected={isActive}
            disabled={!isEnabled}
            className={[styles.tab, isActive ? styles.tabActive : ''].filter(Boolean).join(' ')}
            onClick={() => setActiveChatId(chatId)}
          >
            {CHAT_TITLES[chatId]}
          </button>
        );
      })}
    </div>
  );
};
