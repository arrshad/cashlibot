import { create } from 'zustand';
import { fetchGamification } from '@/api/client';
import type { GamificationStatus } from '@/types';

type GamificationStore = {
  status: GamificationStatus | null;
  loading: boolean;
  error: string | null;
  load: () => Promise<void>;
};

export const useGamificationStore = create<GamificationStore>((set) => ({
  status: null,
  loading: false,
  error: null,

  load: async () => {
    set({ loading: true, error: null });
    try {
      const status = await fetchGamification();
      set({ status, loading: false });
    } catch (err) {
      set({
        loading: false,
        error: err instanceof Error ? err.message : 'failed to load',
      });
    }
  },
}));
