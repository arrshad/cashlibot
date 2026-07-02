import axios from 'axios';
import type {
  CreditAdjustPayload,
  Overview,
  UserDetail,
  UserList,
} from './types';

const API_BASE = import.meta.env.VITE_API_BASE ?? 'http://localhost:8000';

const TOKEN_KEY = 'cashlibot_admin_token';

export function getStoredToken(): string | null {
  return localStorage.getItem(TOKEN_KEY);
}

export function setStoredToken(token: string): void {
  localStorage.setItem(TOKEN_KEY, token);
}

export function clearStoredToken(): void {
  localStorage.removeItem(TOKEN_KEY);
}

const http = axios.create({
  baseURL: API_BASE,
  timeout: 15000,
});

http.interceptors.request.use((config) => {
  const token = getStoredToken();
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

export async function fetchOverview(): Promise<Overview> {
  const { data } = await http.get<Overview>('/api/admin/overview');
  return data;
}

export async function fetchUsers(
  q: string | undefined,
  offset: number,
  limit = 50,
): Promise<UserList> {
  const { data } = await http.get<UserList>('/api/admin/users', {
    params: { q: q || undefined, offset, limit },
  });
  return data;
}

export async function fetchUserDetail(id: number): Promise<UserDetail> {
  const { data } = await http.get<UserDetail>(`/api/admin/users/${id}`);
  return data;
}

export async function adjustCredits(
  id: number,
  payload: CreditAdjustPayload,
): Promise<UserDetail> {
  const { data } = await http.post<UserDetail>(
    `/api/admin/users/${id}/credits`,
    payload,
  );
  return data;
}
