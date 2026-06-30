import axios from 'axios';
import { getInitDataRaw } from '@/telegram';
import type {
  AppConfig,
  Me,
  OnboardingPayload,
  OnboardingResult,
} from '@/types';

// In dev, the Mini App is served on :5173 and the API runs at :8000.
// In prod the Mini App is reverse-proxied to the same origin as the API,
// so the empty-string base just resolves relatively.
const API_BASE = import.meta.env.VITE_API_BASE ?? 'http://localhost:8000';

const http = axios.create({
  baseURL: API_BASE,
  timeout: 15000,
});

http.interceptors.request.use((config) => {
  const initData = getInitDataRaw();
  if (initData) {
    config.headers.Authorization = `tma ${initData}`;
  }
  return config;
});

export async function fetchMe(): Promise<Me> {
  const { data } = await http.get<Me>('/api/me');
  return data;
}

export async function fetchConfig(): Promise<AppConfig> {
  const { data } = await http.get<AppConfig>('/api/config');
  return data;
}

export async function completeOnboarding(
  payload: OnboardingPayload,
): Promise<OnboardingResult> {
  const { data } = await http.post<OnboardingResult>(
    '/api/onboarding/complete',
    payload,
  );
  return data;
}
