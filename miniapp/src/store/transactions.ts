import { create } from 'zustand';
import {
  createTransaction as apiCreate,
  deleteTransaction as apiDelete,
  fetchTransactions,
} from '@/api/client';
import { useDashboardStore } from '@/store/dashboard';
import type {
  Transaction,
  TransactionCreatePayload,
  TransactionListFilters,
} from '@/types';

type TransactionsStore = {
  items: Transaction[];
  loading: boolean;
  error: string | null;
  load: (filters?: TransactionListFilters) => Promise<void>;
  create: (payload: TransactionCreatePayload) => Promise<Transaction>;
  remove: (id: string) => Promise<void>;
};

async function refreshDashboardEcho(): Promise<void> {
  // Balances + summary have shifted — pull them again so every open view
  // shows consistent numbers.
  await useDashboardStore.getState().load();
}

export const useTransactionsStore = create<TransactionsStore>((set, get) => ({
  items: [],
  loading: false,
  error: null,

  load: async (filters) => {
    set({ loading: true, error: null });
    try {
      const items = await fetchTransactions(filters);
      set({ items, loading: false });
    } catch (err) {
      const message = err instanceof Error ? err.message : 'failed to load';
      set({ loading: false, error: message });
    }
  },

  create: async (payload) => {
    const tx = await apiCreate(payload);
    set({ items: [tx, ...get().items] });
    await refreshDashboardEcho();
    return tx;
  },

  remove: async (id) => {
    await apiDelete(id);
    set({ items: get().items.filter((t) => t.id !== id) });
    await refreshDashboardEcho();
  },
}));
