import { useState } from 'react';

import CheckIcon from '@mui/icons-material/Check';
import VisibilityIcon from '@mui/icons-material/Visibility';
import VisibilityOffIcon from '@mui/icons-material/VisibilityOff';
import {
  Alert,
  Avatar,
  Box,
  Button,
  Card,
  CardContent,
  Chip,
  CircularProgress,
  IconButton,
  InputAdornment,
  TextField,
  Typography,
} from '@mui/material';

import { PROVIDERS, type ProviderId } from './entity';
import { useGetSettings, useUpdateSettings } from './query';

import styles from './ProviderSettings.module.scss';

export const ProviderSettings = () => {
  const { data, isLoading, isError } = useGetSettings();
  const update = useUpdateSettings();

  const [keyInputs, setKeyInputs] = useState<Partial<Record<ProviderId, string>>>({});
  const [showKeys, setShowKeys] = useState<Partial<Record<ProviderId, boolean>>>({});

  if (isLoading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', pt: 8 }}>
        <CircularProgress />
      </Box>
    );
  }

  if (isError || !data) {
    return (
      <Box sx={{ p: 3 }}>
        <Alert severity="error">Не удалось загрузить настройки провайдеров</Alert>
      </Box>
    );
  }

  const { provider: activeProvider, keyStatus = {} as Record<ProviderId, boolean> } = data;

  const handleSelect = (id: ProviderId) => {
    if (id === activeProvider || update.isPending) return;
    update.mutate({ provider: id });
  };

  const handleSaveKey = (id: ProviderId) => {
    const key = (keyInputs[id] ?? '').trim();
    if (!key) return;
    update.mutate(
      { provider: id, apiKey: key },
      { onSuccess: () => setKeyInputs(prev => ({ ...prev, [id]: '' })) },
    );
  };

  const handleRemoveKey = (id: ProviderId) => {
    update.mutate({ provider: id, apiKey: '' });
  };

  const toggleShowKey = (id: ProviderId) =>
    setShowKeys(prev => ({ ...prev, [id]: !prev[id] }));

  return (
    <Box className={styles.root}>
      <Typography variant="h6" sx={{ mb: 0.5, fontWeight: 600 }}>
        AI Провайдеры
      </Typography>
      <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
        Выберите провайдера и укажите API ключ для каждого, которым хотите пользоваться.
      </Typography>

      <Box className={styles.grid}>
        {PROVIDERS.map(p => {
          const isActive = p.id === activeProvider;
          const hasKey = keyStatus[p.id];
          const inputVal = keyInputs[p.id] ?? '';
          const showKey = showKeys[p.id] ?? false;

          return (
            <Card
              key={p.id}
              variant="outlined"
              className={`${styles.card} ${isActive ? styles.cardActive : ''}`}
            >
              <CardContent className={styles.cardContent}>

                {/* Header: avatar + name + badge */}
                <Box className={styles.cardHeader}>
                  <Avatar sx={{ bgcolor: p.color, width: 40, height: 40, fontSize: 17, fontWeight: 700 }}>
                    {p.initial}
                  </Avatar>
                  <Box sx={{ flex: 1, minWidth: 0 }}>
                    <Typography variant="subtitle2" noWrap>{p.name}</Typography>
                    <Typography variant="caption" color="text.secondary" noWrap>
                      {p.description}
                    </Typography>
                  </Box>
                  {isActive && (
                    <Chip
                      label="Активен"
                      color="primary"
                      size="small"
                      icon={<CheckIcon sx={{ fontSize: '13px !important' }} />}
                    />
                  )}
                </Box>

                {/* API key row */}
                <Box className={styles.keyRow}>
                  <TextField
                    fullWidth
                    variant="outlined"
                    placeholder={hasKey ? '••••••••••••••••' : 'API ключ'}
                    value={inputVal}
                    onChange={e =>
                      setKeyInputs(prev => ({ ...prev, [p.id]: e.target.value }))
                    }
                    type={showKey ? 'text' : 'password'}
                    size="small"
                    onKeyDown={e => e.key === 'Enter' && handleSaveKey(p.id)}
                    InputProps={{
                      endAdornment: (
                        <InputAdornment position="end">
                          <IconButton size="small" edge="end" onClick={() => toggleShowKey(p.id)}>
                            {showKey
                              ? <VisibilityOffIcon sx={{ fontSize: 16 }} />
                              : <VisibilityIcon sx={{ fontSize: 16 }} />}
                          </IconButton>
                        </InputAdornment>
                      ),
                    }}
                  />
                  {inputVal.trim() ? (
                    <Button
                      size="small"
                      variant="contained"
                      disableElevation
                      disabled={update.isPending}
                      onClick={() => handleSaveKey(p.id)}
                      sx={{ whiteSpace: 'nowrap', flexShrink: 0 }}
                    >
                      Сохранить
                    </Button>
                  ) : hasKey ? (
                    <Button
                      size="small"
                      variant="outlined"
                      color="error"
                      disabled={update.isPending}
                      onClick={() => handleRemoveKey(p.id)}
                      sx={{ whiteSpace: 'nowrap', flexShrink: 0 }}
                    >
                      Удалить
                    </Button>
                  ) : null}
                </Box>

                {/* Select button */}
                {!isActive && (
                  <Button
                    fullWidth
                    size="small"
                    variant="outlined"
                    disableElevation
                    disabled={update.isPending}
                    onClick={() => handleSelect(p.id)}
                    sx={{ mt: 0.5 }}
                  >
                    Выбрать
                  </Button>
                )}
              </CardContent>
            </Card>
          );
        })}
      </Box>
    </Box>
  );
};
