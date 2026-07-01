import { create } from 'zustand';
import {
  contributeToGoal as apiContribute,
  createGoal as apiCreate,
  deleteGoal as apiDelete,
  fetchGoals,
} from '@/api/client';
import type {
  ContributeResult,
  SavingsGoal,
  SavingsGoalCreatePayload,
} from '@/types';

type GoalsStore = {
  items: SavingsGoal[];
  loading: boolean;
  error: string | null;
  load: () => Promise<void>;
  create: (payload: SavingsGoalCreatePayload) => Promise<SavingsGoal>;
  contribute: (id: string, amount: string) => Promise<ContributeResult>;
  remove: (id: string) => Promise<void>;
};

export const useGoalsStore = create<GoalsStore>((set, get) => ({
  items: [],
  loading: false,
  error: null,

  load: async () => {
    set({ loading: true, error: null });
    try {
      const items = await fetchGoals();
      set({ items, loading: false });
    } catch (err) {
      set({
        loading: false,
        error: err instanceof Error ? err.message : 'failed to load',
      });
    }
  },

  create: async (payload) => {
    const goal = await apiCreate(payload);
    set({ items: [...get().items, goal] });
    return goal;
  },

  contribute: async (id, amount) => {
    const result = await apiContribute(id, { amount });
    set({
      items: get().items.map((g) => (g.id === id ? result.goal : g)),
    });
    return result;
  },

  remove: async (id) => {
    await apiDelete(id);
    set({ items: get().items.filter((g) => g.id !== id) });
  },
}));
