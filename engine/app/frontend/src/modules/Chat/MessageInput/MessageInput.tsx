import { useRef, useState } from 'react';

import { useProjectStore } from '@/stores/project.store';
import { useWorkspaceStore } from '@/stores/workspace.store';

import { CHAT_AGENTS } from '../constants/agents';
import { useSendMessage } from '../query';
import { useChatStore } from '../store';

import { MentionDropdown } from './MentionDropdown';

import styles from './MessageInput.module.scss';

function getActiveMention(
  text: string,
  cursor: number,
): { start: number; query: string } | null {
  const before = text.slice(0, cursor);
  const match = before.match(/@([\w-]*)$/);
  if (!match) return null;
  // Группа в паттерне обязательная, но при noUncheckedIndexedAccess
  // доступ по индексу всё равно даёт string | undefined.
  const query = match[1] ?? '';
  return { start: before.length - match[0].length, query: query.toLowerCase() };
}

function extractMentions(text: string): string[] {
  const matches = text.match(/@([\w-]+)/g) ?? [];
  return [...new Set(matches.map((m) => m.slice(1)))];
}

export const MessageInput = () => {
  const projectId = useProjectStore((s) => s.selectedProjectId);
  const activeChatId = useWorkspaceStore((s) => s.activeChatId);
  const enabledChats = useWorkspaceStore((s) => s.enabledChats);
  const draft = useChatStore((s) => (activeChatId ? s.inputDraft[activeChatId] ?? '' : ''));
  const setInputDraft = useChatStore((s) => s.setInputDraft);
  const sendMessage = useSendMessage(projectId, activeChatId);

  const inputRef = useRef<HTMLInputElement>(null);
  const [dropdownIndex, setDropdownIndex] = useState(0);
  const [cursorPos, setCursorPos] = useState(0);

  const isDisabled = !activeChatId || !enabledChats.has(activeChatId);

  const agents = activeChatId ? (CHAT_AGENTS[activeChatId] ?? []) : [];
  const activeMention = getActiveMention(draft, cursorPos);
  const filtered = activeMention
    ? agents.filter(
        (a) =>
          a.id.toLowerCase().includes(activeMention.query) ||
          a.title.toLowerCase().includes(activeMention.query),
      )
    : [];
  const showDropdown = filtered.length > 0;

  const handleSelect = (agent: { id: string }) => {
    if (!activeChatId || !activeMention) return;
    const before = draft.slice(0, activeMention.start);
    const after = draft.slice(inputRef.current?.selectionStart ?? draft.length);
    const next = `${before}@${agent.id} ${after}`;
    setInputDraft(activeChatId, next);
    setDropdownIndex(0);
    // Restore focus
    requestAnimationFrame(() => {
      const el = inputRef.current;
      if (!el) return;
      const pos = (before + `@${agent.id} `).length;
      el.setSelectionRange(pos, pos);
      el.focus();
    });
  };

  const handleClose = () => setDropdownIndex(0);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (!activeChatId) return;
    setInputDraft(activeChatId, e.target.value);
    setCursorPos(e.target.selectionStart ?? e.target.value.length);
    setDropdownIndex(0);
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (!showDropdown) return;

    if (e.key === 'ArrowDown') {
      e.preventDefault();
      setDropdownIndex((i) => (i + 1) % filtered.length);
    } else if (e.key === 'ArrowUp') {
      e.preventDefault();
      setDropdownIndex((i) => (i - 1 + filtered.length) % filtered.length);
    } else if (e.key === 'Enter' || e.key === 'Tab') {
      e.preventDefault();
      // Список мог опустеть между рендером и нажатием клавиши.
      const agent = filtered[dropdownIndex];
      if (agent) handleSelect(agent);
    } else if (e.key === 'Escape') {
      e.preventDefault();
      handleClose();
    }
  };

  const handleSubmit = (event: React.FormEvent) => {
    event.preventDefault();
    if (isDisabled || !activeChatId || !draft.trim() || showDropdown) return;
    const mentions = extractMentions(draft);
    sendMessage.mutate({ content: draft, mentions });
    setInputDraft(activeChatId, '');
  };

  return (
    <form className={styles.root} onSubmit={handleSubmit} style={{ position: 'relative' }}>
      {showDropdown && (
        <MentionDropdown
          agents={filtered}
          activeIndex={dropdownIndex}
          onSelect={handleSelect}
          onClose={handleClose}
        />
      )}
      <input
        ref={inputRef}
        className={styles.input}
        type="text"
        value={draft}
        disabled={isDisabled}
        placeholder={isDisabled ? 'Чат недоступен' : 'Сообщение · @ для упоминания агента'}
        onChange={handleChange}
        onKeyDown={handleKeyDown}
      />
      <button className={styles.button} type="submit" disabled={isDisabled || !draft.trim()}>
        Отправить
      </button>
    </form>
  );
};
