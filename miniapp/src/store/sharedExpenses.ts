import { create } from 'zustand';
import {
  approveSplit as apiApprove,
  createSharedExpense as apiCreate,
  disputeSplit as apiDispute,
  fetchFriendBalance,
  fetchSharedExpenses,
  settleWithFriend,
} from '@/api/client';
import type {
  FriendBalance,
  SharedExpense,
  SharedExpenseCreatePayload,
  SharedExpensesOverview,
} from '@/types';

type State = {
  overview: SharedExpensesOverview | null;
  balances: Record<number, FriendBalance>;
  loading: boolean;
  error: string | null;
  loadOverview: () => Promise<void>;
  loadBalance: (friendId: number) => Promise<void>;
  create: (payload: SharedExpenseCreatePayload) => Promise<SharedExpense>;
  approve: (splitId: string) => Promise<void>;
  dispute: (splitId: string) => Promise<void>;
  settle: (friendId: number) => Promise<number>;
};

export const useSharedExpensesStore = create<State>((set, get) => ({
  overview: null,
  balances: {},
  loading: false,
  error: null,

  loadOverview: async () => {
    set({ loading: true, error: null });
    try {
      const overview = await fetchSharedExpenses();
      set({ overview, loading: false });
    } catch (err) {
      set({
        loading: false,
        error: err instanceof Error ? err.message : 'failed to load',
      });
    }
  },

  loadBalance: async (friendId) => {
    const balance = await fetchFriendBalance(friendId);
    set({ balances: { ...get().balances, [friendId]: balance } });
  },

  create: async (payload) => {
    const expense = await apiCreate(payload);
    // Refresh anything that might be stale.
    await get().loadOverview();
    return expense;
  },

  approve: async (splitId) => {
    await apiApprove(splitId);
    await get().loadOverview();
  },

  dispute: async (splitId) => {
    await apiDispute(splitId);
    await get().loadOverview();
  },

  settle: async (friendId) => {
    const { splits_settled } = await settleWithFriend(friendId);
    await get().loadBalance(friendId);
    return splits_settled;
  },
}));
