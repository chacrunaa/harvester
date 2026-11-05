import { tauriRpc } from '@/app/clients/tauriRpc';

const isTauri = typeof window !== 'undefined' && '__TAURI__' in window;

async function fetchHttp<T>(method: string, url: string, body?: unknown): Promise<T> {
  const resp = await fetch(url, {
    method,
    headers: body !== undefined ? { 'Content-Type': 'application/json' } : undefined,
    body: body !== undefined ? JSON.stringify(body) : undefined,
  });
  if (!resp.ok) {
    const text = await resp.text().catch(() => resp.statusText);
    throw new Error(`HTTP ${resp.status}: ${text}`);
  }
  return resp.json() as Promise<T>;
}

async function get<T>(url: string): Promise<T> {
  if (isTauri) return tauriRpc<T>('GET', url);
  return fetchHttp<T>('GET', url);
}

async function post<T>(url: string, body?: unknown): Promise<T> {
  if (isTauri) return tauriRpc<T>('POST', url, body);
  return fetchHttp<T>('POST', url, body);
}

export const http = { get, post };
