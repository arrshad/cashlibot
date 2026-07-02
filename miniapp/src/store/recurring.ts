import { create } from 'zustand';
import {
  createRecurring as apiCreate,
  deleteRecurring as apiDelete,
  fetchRecurring,
} from '@/api/client';
import type { RecurringCreatePayload, RecurringTemplate } from '@/types';

type RecurringStore = {
  items: RecurringTemplate[];
  loading: boolean;
  error: string | null;
  load: () => Promise<void>;
  create: (payload: RecurringCreatePayload) => Promise<RecurringTemplate>;
  remove: (id: string) => Promise<void>;
};

export const useRecurringStore = create<RecurringStore>((set, get) => ({
  items: [],
  loading: false,
  error: null,

  load: async () => {
    set({ loading: true, error: null });
    try {
      const items = await fetchRecurring();
      set({ items, loading: false });
    } catch (err) {
      set({
        loading: false,
        error: err instanceof Error ? err.message : 'failed to load',
      });
    }
  },

  create: async (payload) => {
    const template = await apiCreate(payload);
    const next = [...get().items, template].sort((a, b) =>
      a.next_due_date.localeCompare(b.next_due_date),
    );
    set({ items: next });
    return template;
  },

  remove: async (id) => {
    await apiDelete(id);
    set({ items: get().items.filter((r) => r.id !== id) });
  },
}));
