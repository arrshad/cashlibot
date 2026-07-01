import { create } from 'zustand';
import {
  createBudget as apiCreate,
  deleteBudget as apiDelete,
  fetchBudgets,
} from '@/api/client';
import type { Budget, BudgetCreatePayload } from '@/types';

type BudgetsStore = {
  items: Budget[];
  loading: boolean;
  error: string | null;
  load: () => Promise<void>;
  create: (payload: BudgetCreatePayload) => Promise<Budget>;
  remove: (id: string) => Promise<void>;
};

export const useBudgetsStore = create<BudgetsStore>((set, get) => ({
  items: [],
  loading: false,
  error: null,

  load: async () => {
    set({ loading: true, error: null });
    try {
      const items = await fetchBudgets();
      set({ items, loading: false });
    } catch (err) {
      set({
        loading: false,
        error: err instanceof Error ? err.message : 'failed to load',
      });
    }
  },

  create: async (payload) => {
    const budget = await apiCreate(payload);
    const existingIdx = get().items.findIndex((b) => b.id === budget.id);
    if (existingIdx >= 0) {
      // create_budget upserts on (category, period); reflect the updated row.
      const next = [...get().items];
      next[existingIdx] = budget;
      set({ items: next });
    } else {
      set({ items: [...get().items, budget] });
    }
    return budget;
  },

  remove: async (id) => {
    await apiDelete(id);
    set({ items: get().items.filter((b) => b.id !== id) });
  },
}));
