import { create } from 'zustand';
import {
  archiveAccount as apiArchiveAccount,
  createAccount as apiCreateAccount,
  fetchAccounts,
  fetchDashboardSummary,
} from '@/api/client';
import type { Account, AccountCreatePayload, DashboardSummary } from '@/types';

type DashboardStore = {
  accounts: Account[];
  summary: DashboardSummary | null;
  loading: boolean;
  error: string | null;
  load: () => Promise<void>;
  createAccount: (payload: AccountCreatePayload) => Promise<Account>;
  archiveAccount: (id: string) => Promise<void>;
};

export const useDashboardStore = create<DashboardStore>((set, get) => ({
  accounts: [],
  summary: null,
  loading: false,
  error: null,

  load: async () => {
    set({ loading: true, error: null });
    try {
      const [accounts, summary] = await Promise.all([
        fetchAccounts(),
        fetchDashboardSummary(),
      ]);
      set({ accounts, summary, loading: false });
    } catch (err) {
      const message = err instanceof Error ? err.message : 'failed to load';
      set({ loading: false, error: message });
    }
  },

  createAccount: async (payload) => {
    const account = await apiCreateAccount(payload);
    // Re-fetch the summary too because per-currency totals may have shifted.
    const summary = await fetchDashboardSummary();
    set({ accounts: [...get().accounts, account], summary });
    return account;
  },

  archiveAccount: async (id) => {
    await apiArchiveAccount(id);
    const summary = await fetchDashboardSummary();
    set({
      accounts: get().accounts.filter((a) => a.id !== id),
      summary,
    });
  },
}));
