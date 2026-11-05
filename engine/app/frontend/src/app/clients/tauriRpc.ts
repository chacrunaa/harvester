import { invoke } from '@tauri-apps/api/core';

/**
 * Маппинг REST URL → JSON-RPC method + params для десктоп-режима:
 * http.ts вызывает tauriRpc(), тот через invoke('rpc') идёт в sidecar.
 *
 * Внимание: десктоп-режим не достроен — sidecar, говорящий по stdio
 * JSON-RPC, не собирается. См. раздел «Про Tauri» в app/README.md.
 */

type Verb = 'GET' | 'POST';

/**
 * Доступ к захваченным группам regex по индексу. Паттерны ниже не
 * используют необязательных групп, поэтому при совпадении группа всегда
 * есть; resolveRoute проверяет это в рантайме и бросает ошибку, если
 * паттерн и обработчик разошлись.
 */
type GroupAccessor = (index: number) => string;

type RouteEntry = {
  verb: Verb;
  pattern: RegExp;
  build: (group: GroupAccessor) => { method: string; pathParams: Record<string, string> };
};

const ROUTES: RouteEntry[] = [
  // Pipeline
  {
    verb: 'GET',
    pattern: /^\/api\/pipeline\/state$/,
    build: () => ({ method: 'pipeline:getState', pathParams: {} }),
  },
  {
    verb: 'POST',
    pattern: /^\/api\/pipeline\/([^/]+)\/ok$/,
    build: (group) => ({ method: 'pipeline:ok', pathParams: { phase: group(0) } }),
  },
  {
    verb: 'POST',
    pattern: /^\/api\/pipeline\/([^/]+)\/notok$/,
    build: (group) => ({ method: 'pipeline:notok', pathParams: { phase: group(0) } }),
  },
  {
    verb: 'POST',
    pattern: /^\/api\/pipeline\/agents\/([^/]+)\/retry$/,
    build: (group) => ({ method: 'pipeline:agent:retry', pathParams: { agent: group(0) } }),
  },
  {
    verb: 'POST',
    pattern: /^\/api\/pipeline\/agents\/([^/]+)\/skip$/,
    build: (group) => ({ method: 'pipeline:agent:skip', pathParams: { agent: group(0) } }),
  },
  {
    verb: 'POST',
    pattern: /^\/api\/pipeline\/export-docs$/,
    build: () => ({ method: 'pipeline:export-docs', pathParams: {} }),
  },

  // Projects
  {
    verb: 'GET',
    pattern: /^\/api\/projects$/,
    build: () => ({ method: 'projects:list', pathParams: {} }),
  },
  {
    verb: 'POST',
    pattern: /^\/api\/projects\/open$/,
    build: () => ({ method: 'projects:open', pathParams: {} }),
  },
  {
    verb: 'POST',
    pattern: /^\/api\/projects$/,
    build: () => ({ method: 'projects:create', pathParams: {} }),
  },

  // Agents
  {
    verb: 'POST',
    pattern: /^\/api\/agents\/(.+)\/trigger$/,
    build: (group) => ({ method: 'agents:trigger', pathParams: { agentId: group(0) } }),
  },

  // Qna
  {
    verb: 'GET',
    pattern: /^\/api\/qna\/pending$/,
    build: () => ({ method: 'qna:listPending', pathParams: {} }),
  },
  {
    verb: 'POST',
    pattern: /^\/api\/qna\/(.+)\/answer$/,
    build: (group) => ({ method: 'qna:answer', pathParams: { agentId: group(0) } }),
  },

  // Chats
  {
    verb: 'GET',
    pattern: /^\/api\/chats\/([^/]+)$/,
    build: (group) => ({ method: 'chats:get', pathParams: { phase: group(0) } }),
  },
  {
    verb: 'POST',
    pattern: /^\/api\/chats\/([^/]+)$/,
    build: (group) => ({ method: 'chats:post', pathParams: { phase: group(0) } }),
  },

  // Tasks
  {
    verb: 'GET',
    pattern: /^\/api\/tasks$/,
    build: () => ({ method: 'tasks:list', pathParams: {} }),
  },
  {
    verb: 'POST',
    pattern: /^\/api\/tasks$/,
    build: () => ({ method: 'tasks:create', pathParams: {} }),
  },

  // Settings
  {
    verb: 'GET',
    pattern: /^\/api\/settings$/,
    build: () => ({ method: 'settings:get', pathParams: {} }),
  },
  {
    verb: 'POST',
    pattern: /^\/api\/settings$/,
    build: () => ({ method: 'settings:update', pathParams: {} }),
  },
];

function resolveRoute(verb: Verb, url: string): { method: string; pathParams: Record<string, string> } {
  // Отрезать query string. split всегда возвращает хотя бы один элемент,
  // но при noUncheckedIndexedAccess это надо показать типам явно.
  const path = url.split('?')[0] ?? url;

  for (const route of ROUTES) {
    if (route.verb !== verb) continue;

    const match = route.pattern.exec(path);
    if (!match) continue;

    const groups = match.slice(1);
    const group: GroupAccessor = (index) => {
      const value = groups[index];
      if (typeof value !== 'string') {
        throw new Error(`Route ${String(route.pattern)} has no capture group ${index} for ${path}`);
      }
      return value;
    };

    return route.build(group);
  }

  throw new Error(`No RPC route for ${verb} ${url}`);
}

export async function tauriRpc<T>(verb: Verb, url: string, body?: unknown): Promise<T> {
  const { method, pathParams } = resolveRoute(verb, url);
  const params = {
    ...pathParams,
    ...(body && typeof body === 'object' ? (body as Record<string, unknown>) : {}),
  };
  return invoke<T>('rpc', { method, params });
}
