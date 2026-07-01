import { create } from 'zustand';
import { fetchCredits } from '@/api/client';
import type { CreditsStatus } from '@/types';

type CreditsStore = {
  status: CreditsStatus | null;
  loading: boolean;
  error: string | null;
  load: () => Promise<void>;
};

export const useCreditsStore = create<CreditsStore>((set) => ({
  status: null,
  loading: false,
  error: null,

  load: async () => {
    set({ loading: true, error: null });
    try {
      const status = await fetchCredits();
      set({ status, loading: false });
    } catch (err) {
      set({
        loading: false,
        error: err instanceof Error ? err.message : 'failed to load',
      });
    }
  },
}));
