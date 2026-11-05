import { createBrowserRouter, Navigate } from 'react-router-dom';

import { ROUTES } from '@/constants/routes';
import {
  DocumentationPage,
  NotFoundPage,
  ProfilePage,
  ProvidersPage,
  WorkspacePage,
} from '@/pages';

import { AppLayout } from './layouts/AppLayout';
import { SettingsLayout } from './layouts/SettingsLayout';

export const router = createBrowserRouter([
  {
    element: <AppLayout />,
    children: [
      { path: ROUTES.workspace, element: <WorkspacePage /> },
      { path: ROUTES.docs, element: <DocumentationPage /> },
    ],
  },
  {
    path: ROUTES.settings,
    element: <SettingsLayout />,
    children: [
      { index: true, element: <Navigate to={ROUTES.settingsProfile} replace /> },
      { path: ROUTES.settingsProfile, element: <ProfilePage /> },
      { path: ROUTES.settingsProviders, element: <ProvidersPage /> },
    ],
  },
  { path: '*', element: <NotFoundPage /> },
]);
