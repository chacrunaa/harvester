export const ROUTES = {
  workspace: '/',
  docs: '/docs',
  help: '/help',
  settings: '/settings',
  settingsProfile: '/settings/profile',
  settingsProviders: '/settings/providers',
} as const;

export type RouteKey = keyof typeof ROUTES;
export type RoutePath = (typeof ROUTES)[RouteKey];
