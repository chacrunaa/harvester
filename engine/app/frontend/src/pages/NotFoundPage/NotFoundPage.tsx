import { Button } from '@mui/material';
import { useNavigate } from 'react-router-dom';

import { ROUTES } from '@/constants/routes';

import styles from './NotFoundPage.module.scss';

export const NotFoundPage = () => {
  const navigate = useNavigate();
  return (
    <main className={styles.root}>
      <div className={styles.card}>
        <h1 className={styles.title}>404</h1>
        <p className={styles.text}>Страница не найдена</p>
        <Button variant="contained" onClick={() => navigate(ROUTES.workspace)}>
          На главную
        </Button>
      </div>
    </main>
  );
};
