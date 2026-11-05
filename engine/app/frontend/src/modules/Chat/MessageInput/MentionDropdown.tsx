import { useEffect } from 'react';

import type { Agent } from '../constants/agents';

import styles from './MentionDropdown.module.scss';

type Props = {
  agents: Agent[];
  activeIndex: number;
  onSelect: (agent: Agent) => void;
  onClose: () => void;
};

export const MentionDropdown = ({ agents, activeIndex, onSelect, onClose }: Props) => {
  useEffect(() => {
    const handler = (e: MouseEvent) => {
      const root = document.getElementById('mention-dropdown');
      if (root && !root.contains(e.target as Node)) onClose();
    };
    document.addEventListener('mousedown', handler);
    return () => document.removeEventListener('mousedown', handler);
  }, [onClose]);

  if (agents.length === 0) return null;

  return (
    <div id="mention-dropdown" className={styles.root} role="listbox">
      {agents.map((agent, i) => (
        <button
          key={agent.id}
          type="button"
          role="option"
          aria-selected={i === activeIndex}
          className={[styles.item, i === activeIndex ? styles.active : ''].filter(Boolean).join(' ')}
          onMouseDown={(e) => {
            e.preventDefault(); // keep focus on input
            onSelect(agent);
          }}
        >
          <span className={styles.mention}>@{agent.id}</span>
          <span className={styles.title}>{agent.title}</span>
        </button>
      ))}
    </div>
  );
};
