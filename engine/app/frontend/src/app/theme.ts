import { createTheme } from '@mui/material/styles';

export const theme = createTheme({
  palette: {
    mode: 'light',
    primary: { main: '#1976d2' },
    secondary: { main: '#9c27b0' },
    info: { main: '#0288d1' },
    success: { main: '#2e7d32' },
    error: { main: '#d32f2f', dark: '#d32f2f' },
    background: { default: '#ffffff', paper: '#ffffff' },
    text: {
      primary: 'rgba(0, 0, 0, 0.87)',
      secondary: 'rgba(0, 0, 0, 0.6)',
      disabled: 'rgba(0, 0, 0, 0.38)',
    },
    action: { disabled: 'rgba(0, 0, 0, 0.26)' },
  },
  shape: { borderRadius: 4 },
  typography: {
    fontFamily:
      'system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Oxygen, Ubuntu, Cantarell, "Helvetica Neue", sans-serif',
    overline: {
      fontSize: 12,
      fontWeight: 400,
      lineHeight: 2.66,
      letterSpacing: '1px',
      textTransform: 'uppercase',
    },
    subtitle2: {
      fontSize: 14,
      fontWeight: 500,
      lineHeight: 1.57,
      letterSpacing: '0.1px',
    },
    body2: {
      fontSize: 14,
      fontWeight: 400,
      lineHeight: 1.43,
      letterSpacing: '0.17px',
    },
    caption: {
      fontSize: 12,
      fontWeight: 400,
      lineHeight: 1.5,
      letterSpacing: '0.15px',
    },
    button: {
      fontSize: 13,
      fontWeight: 500,
      lineHeight: '22px',
      letterSpacing: '0.46px',
      textTransform: 'uppercase',
    },
  },
  components: {
    MuiButton: {
      defaultProps: { size: 'small' },
    },
    MuiChip: {
      defaultProps: { size: 'small' },
      styleOverrides: {
        root: { borderRadius: '100px' },
      },
    },
    MuiTextField: {
      defaultProps: { size: 'small', variant: 'standard' },
    },
    MuiAvatar: {
      styleOverrides: {
        root: {
          backgroundColor: '#bdbdbd',
          fontSize: 20,
          letterSpacing: '0.14px',
        },
      },
    },
    MuiAlert: {
      styleOverrides: {
        outlinedInfo: { borderColor: '#0288d1' },
      },
    },
  },
});
