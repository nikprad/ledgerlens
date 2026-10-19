/**
 * HTTP Client to communicate with Python FastAPI backend.
 */

import dotenv from 'dotenv';
dotenv.config();

export const BACKEND_URL = process.env.BACKEND_URL || 'http://127.0.0.1:8000';

export async function callBackend<T = any>(endpoint: string, options: RequestInit = {}): Promise<T> {
  const url = `${BACKEND_URL.replace(/\/$/, '')}/${endpoint.replace(/^\//, '')}`;
  const headers = {
    'Content-Type': 'application/json',
    ...(options.headers || {}),
  };

  const res = await fetch(url, {
    ...options,
    headers,
  });

  if (!res.ok) {
    const errorText = await res.text();
    throw new Error(`Backend call to ${endpoint} failed (${res.status}): ${errorText}`);
  }

  return (await res.json()) as T;
}
