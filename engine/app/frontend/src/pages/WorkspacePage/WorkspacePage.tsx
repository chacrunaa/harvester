import { Chat } from '@/modules';

import styles from './WorkspacePage.module.scss';

export const WorkspacePage = () => (
  <div className={styles.root}>
    <section className={styles.activeChat}>
      <header className={styles.activeChatHeader} />
      <div className={styles.activeChatBody}>
        <Chat />
      </div>
    </section>
    <section className={styles.reportAndStatus}>
      <section className={styles.statusZone}>
        <header className={styles.sectionHeader}>Состояние</header>
        <div className={styles.statusBody}>
          <span className={styles.placeholder}>StatusPanel module placeholder</span>
        </div>
      </section>
      <section className={styles.reportsZone}>
        <header className={styles.sectionHeader}>Отчёты</header>
        <div className={styles.reportsBody}>
          <span className={styles.placeholder}>ReportsPanel module placeholder</span>
        </div>
      </section>
    </section>
  </div>
);
