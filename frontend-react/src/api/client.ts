import axios from 'axios';
import type { Holding, AddHoldingPayload, ChatResponse } from '../types';
import { supabase } from '../lib/supabase';

const BACKEND_URL = import.meta.env.VITE_BACKEND_URL || 'http://localhost:8000';

export const api = axios.create({
  baseURL: `${BACKEND_URL}/api/v1`,
  timeout: 30000,
});

api.interceptors.request.use(async (config) => {
  const { data: { session } } = await supabase.auth.getSession();
  if (session?.access_token) {
    config.headers.Authorization = `Bearer ${session.access_token}`;
  }
  return config;
});

export const getPortfolio = () =>
  api.get<Holding[]>('/portfolio');

export const addHolding = (payload: AddHoldingPayload) =>
  api.post<Holding>('/portfolio', payload);

export const deleteHolding = (ticker: string) =>
  api.delete(`/portfolio/${ticker}`);

export const syncAlpaca = () =>
  api.post<Holding[]>('/portfolio/sync-alpaca', {});

export const uploadCsv = (file: File) => {
  const form = new FormData();
  form.append('file', file);
  return api.post<Holding[]>('/portfolio/upload-csv', form, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });
};

export interface ChatHolding {
  ticker: string;
  quantity: number;
  avg_buy_price: number;
}

export async function streamChat(
  message: string,
  portfolio_holdings: ChatHolding[] | undefined,
  onToken: (token: string) => void,
  onDone: (sources: string[]) => void,
  onError: (message: string) => void,
): Promise<void> {
  const { data: { session } } = await supabase.auth.getSession();

  let response: Response;
  try {
    response = await fetch(`${BACKEND_URL}/api/v1/chat`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...(session?.access_token ? { Authorization: `Bearer ${session.access_token}` } : {}),
      },
      body: JSON.stringify({ message, portfolio_holdings }),
      signal: AbortSignal.timeout(120_000),
    });
  } catch (err) {
    onError(err instanceof Error ? err.message : 'Network error');
    return;
  }

  if (!response.ok) {
    const body = await response.json().catch(() => ({}));
    onError(body.detail ?? `Request failed (${response.status})`);
    return;
  }

  const reader = response.body!.getReader();
  const decoder = new TextDecoder();
  let buffer = '';

  try {
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      // SSE events are separated by double newlines
      const parts = buffer.split('\n\n');
      buffer = parts.pop() ?? '';

      for (const part of parts) {
        for (const line of part.split('\n')) {
          if (!line.startsWith('data: ')) continue;
          const raw = line.slice(6).trim();
          if (!raw) continue;
          try {
            const event = JSON.parse(raw);
            if (event.type === 'token') onToken(event.text);
            else if (event.type === 'done') onDone(event.sources ?? []);
            else if (event.type === 'error') onError(event.message);
          } catch { /* malformed JSON — skip */ }
        }
      }
    }
  } finally {
    reader.releaseLock();
  }
}
