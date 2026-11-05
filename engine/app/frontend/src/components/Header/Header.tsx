import SettingsIcon from '@mui/icons-material/Settings';
import { Avatar, Button } from '@mui/material';
import { NavLink, useNavigate } from 'react-router-dom';

import { ROUTES } from '@/constants/routes';
import type { WebsocketStatus } from '@/stores/websocket.store';

import styles from './Header.module.scss';

type HeaderProps = {
  wsStatus: WebsocketStatus;
};

const STATUS_LABEL: Record<WebsocketStatus, string> = {
  connecting: 'Подключение…',
  connected: 'Онлайн',
  disconnected: 'Оффлайн',
  error: 'Ошибка',
};

const WS_DOT_CLASS: Record<WebsocketStatus, string | undefined> = {
  connecting: styles.wsDotConnecting,
  connected: styles.wsDotConnected,
  disconnected: styles.wsDotDisconnected,
  error: styles.wsDotError,
};

const navClass = ({ isActive }: { isActive: boolean }) =>
  isActive ? `${styles.link} ${styles.linkActive}` : styles.link;

export const Header = ({ wsStatus }: HeaderProps) => {
  const navigate = useNavigate();

  return (
    <header className={styles.root}>
      <nav className={styles.nav}>
        <NavLink to={ROUTES.workspace} className={navClass}>
          Разработка
        </NavLink>
        <NavLink to={ROUTES.docs} className={navClass}>
          Документация
        </NavLink>
        <NavLink to={ROUTES.help} className={navClass}>
          Инструкция
        </NavLink>
      </nav>
      <div className={styles.profile}>
        <span
          className={`${styles.wsDot} ${WS_DOT_CLASS[wsStatus]}`}
          title={STATUS_LABEL[wsStatus]}
          aria-label={STATUS_LABEL[wsStatus]}
        />
        <Button
          className={styles.settingsButton}
          onClick={() => navigate(ROUTES.settings)}
          aria-label="Настройки"
        >
          <SettingsIcon />
        </Button>
        <Avatar>А</Avatar>
      </div>
    </header>
  );
};
