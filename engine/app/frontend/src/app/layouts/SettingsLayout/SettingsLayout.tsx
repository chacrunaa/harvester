import { NavLink, Outlet, useNavigate } from 'react-router-dom';

import { ROUTES } from '@/constants/routes';

import styles from './SettingsLayout.module.scss';

const navClass = ({ isActive }: { isActive: boolean }) =>
  isActive ? `${styles.navLink} ${styles.navLinkActive}` : styles.navLink;

export const SettingsLayout = () => {
  const navigate = useNavigate();

  return (
    <div className={styles.root}>
      <button
        type="button"
        className={styles.back}
        onClick={() => navigate(ROUTES.workspace)}
      >
        ← Назад
      </button>
      <div className={styles.body}>
        <nav className={styles.nav} aria-label="Разделы настроек">
          <NavLink to={ROUTES.settingsProfile} className={navClass}>
            Профиль
          </NavLink>
          <NavLink to={ROUTES.settingsProviders} className={navClass}>
            Провайдеры
          </NavLink>
        </nav>
        <main className={styles.main}>
          <Outlet />
        </main>
      </div>
    </div>
  );
};
