import { CssBaseline, ThemeProvider } from '@mui/material';
import { QueryClientProvider } from '@tanstack/react-query';
import type { ReactNode } from 'react';

import { queryClient } from './clients/queryClient';
import { theme } from './theme';

type Props = {
  children: ReactNode;
};

export const AppProviders = ({ children }: Props) => (
  <QueryClientProvider client={queryClient}>
    <ThemeProvider theme={theme}>
      <CssBaseline />
      {children}
    </ThemeProvider>
  </QueryClientProvider>
);
