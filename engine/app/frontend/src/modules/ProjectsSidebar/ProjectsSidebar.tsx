import { useState } from 'react';

import ChevronLeftIcon from '@mui/icons-material/ChevronLeft';
import ChevronRightIcon from '@mui/icons-material/ChevronRight';
import {
  Box,
  Button,
  Drawer,
  IconButton,
  List,
  ListItem,
  ListItemButton,
  ListItemText,
  Typography,
} from '@mui/material';

import { useProjectStore } from '@/stores/project.store';

import { useGetProjects } from './query';

const SIDEBAR_WIDTH = 300; // TODO вынести

export const ProjectsSidebar = () => {
  useGetProjects();
  const projects = useProjectStore((s) => s.projects);
  const selectedProjectId = useProjectStore((s) => s.selectedProjectId);
  const setSelectedProject = useProjectStore((s) => s.setSelectedProject);
  const [isOpen, setIsOpen] = useState(true);

  return (
    <Box
      sx={{
        position: 'relative',
        flexShrink: 0,
        width: isOpen ? SIDEBAR_WIDTH : 0,
        transition: 'width 220ms ease',
      }}
    >
      {/* Clip box — скрывает контент Drawer при закрытии */}
      <Box
        sx={{
          width: isOpen ? SIDEBAR_WIDTH : 0,
          height: '100%',
          overflow: 'hidden',
          transition: 'width 220ms ease',
          borderRight: isOpen ? '1px solid #00625a' : 'none',
          borderTopRightRadius: '20px',
          borderBottomRightRadius: '20px',
        }}
      >
        <Drawer
          variant="permanent"
          sx={{ width: '100%', height: '100%' }}
          slotProps={{
            paper: {
              sx: {
                position: 'relative',
                width: SIDEBAR_WIDTH,
                height: '100%',
                border: 'none',
                boxShadow: 'none',
                borderTopRightRadius: '20px',
                borderBottomRightRadius: '20px',
                display: 'flex',
                flexDirection: 'column',
                overflow: 'hidden',
              },
            },
          }}
        >
          <Box sx={{ px: 2, pt: 2, pb: 1 }}>
            <Typography
              variant="overline"
              color="text.secondary"
              sx={{ fontSize: 11, fontWeight: 600, letterSpacing: '0.08em' }}
            >
              Проекты
            </Typography>
          </Box>
          <List disablePadding dense sx={{ flex: 1, overflowY: 'auto' }}>
            {projects.map((project) => (
              <ListItem key={project.id} disablePadding sx={{ px: 1 }}>
                <ListItemButton
                  selected={project.id === selectedProjectId}
                  onClick={() => setSelectedProject(project.id)}
                  sx={{ borderRadius: 1 }}
                >
                  <ListItemText
                    primary={project.name}
                    slotProps={{ primary: { variant: 'body2', noWrap: true } }}
                  />
                </ListItemButton>
              </ListItem>
            ))}
          </List>
          <Box sx={{ p: 2, mt: 'auto' }}>
            <Button
              variant="outlined"
              fullWidth
              disabled
              sx={{
                color: '#4f378a',
                borderColor: '#4f378a',
                '&:hover': {
                  borderColor: '#4f378a',
                  backgroundColor: 'rgba(79, 56, 138, 0.04)',
                },
              }}
            >
              Новый проект
            </Button>
          </Box>
        </Drawer>
      </Box>

      {/* Кнопка раскрытия — position: absolute к контейнеру Drawer */}
      <IconButton
        size="small"
        onClick={() => setIsOpen((o) => !o)}
        aria-label={isOpen ? 'Скрыть проекты' : 'Показать проекты'}
        aria-expanded={isOpen}
        sx={{
          position: 'absolute',
          top: 16,
          left: isOpen ? SIDEBAR_WIDTH : 14,
          transform: 'translateX(-50%)',
          transition: 'left 220ms ease',
          zIndex: 1,
          bgcolor: 'background.paper',
          border: '1px solid #00625a',
          '&:hover': { bgcolor: 'grey.50' },
        }}
      >
        {isOpen ? (
          <ChevronLeftIcon fontSize="small" sx={{ color: '#00625a' }} />
        ) : (
          <ChevronRightIcon fontSize="small" sx={{ color: '#00625a' }} />
        )}
      </IconButton>
    </Box>
  );
};
