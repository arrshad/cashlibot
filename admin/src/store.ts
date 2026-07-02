import { create } from 'zustand';
import {
  clearStoredToken,
  fetchOverview,
  getStoredToken,
  setStoredToken,
} from './api';
import type { Overview } from './types';

type Route =
  | { name: 'overview' }
  | { name: 'users' }
  | { name: 'user'; userId: number };

type AppStore = {
  token: string | null;
  overview: Overview | null;
  overviewLoading: boolean;
  overviewError: string | null;
  route: Route;

  setToken: (token: string) => void;
  logout: () => void;
  go: (route: Route) => void;
  loadOverview: () => Promise<void>;
};

function extractHashToken(): string | null {
  if (typeof window === 'undefined') return null;
  const hash = window.location.hash.slice(1);
  const params = new URLSearchParams(hash);
  return params.get('token');
}

const initialToken = extractHashToken() ?? getStoredToken();
if (initialToken && extractHashToken()) {
  setStoredToken(initialToken);
  // Clean the fragment so a refresh doesn't reopen the login flow.
  window.history.replaceState(null, '', window.location.pathname);
}

export const useAppStore = create<AppStore>((set) => ({
  token: initialToken,
  overview: null,
  overviewLoading: false,
  overviewError: null,
  route: { name: 'overview' },

  setToken: (token) => {
    setStoredToken(token);
    set({ token });
  },
  logout: () => {
    clearStoredToken();
    set({ token: null, overview: null, route: { name: 'overview' } });
  },
  go: (route) => set({ route }),
  loadOverview: async () => {
    set({ overviewLoading: true, overviewError: null });
    try {
      const overview = await fetchOverview();
      set({ overview, overviewLoading: false });
    } catch (err) {
      const message =
        (err as { response?: { status?: number } })?.response?.status === 401
          ? 'unauthorized'
          : err instanceof Error
            ? err.message
            : 'failed to load';
      set({ overviewLoading: false, overviewError: message });
      if (message === 'unauthorized') {
        clearStoredToken();
        set({ token: null });
      }
    }
  },
}));
