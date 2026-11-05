import { Outlet } from 'react-router-dom';

import { Header } from '@/components';
import { ProjectsSidebar } from '@/modules';
import { useWebsocketStore } from '@/stores/websocket.store';

import styles from './AppLayout.module.scss';

export const AppLayout = () => {
  const wsStatus = useWebsocketStore((s) => s.status);

  return (
    <div className={styles.root}>
      <Header wsStatus={wsStatus} />
      <div className={styles.body}>
        <ProjectsSidebar />
        <main className={styles.main}>
          <div className={styles.mainInner}>
            <Outlet />
          </div>
        </main>
      </div>
    </div>
  );
};
