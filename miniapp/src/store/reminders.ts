import { create } from 'zustand';
import {
  createReminder as apiCreate,
  deleteReminder as apiDelete,
  fetchReminders,
} from '@/api/client';
import type { Reminder, ReminderCreatePayload } from '@/types';

type RemindersStore = {
  items: Reminder[];
  loading: boolean;
  error: string | null;
  load: () => Promise<void>;
  create: (payload: ReminderCreatePayload) => Promise<Reminder>;
  remove: (id: string) => Promise<void>;
};

export const useRemindersStore = create<RemindersStore>((set, get) => ({
  items: [],
  loading: false,
  error: null,

  load: async () => {
    set({ loading: true, error: null });
    try {
      const items = await fetchReminders();
      set({ items, loading: false });
    } catch (err) {
      set({
        loading: false,
        error: err instanceof Error ? err.message : 'failed to load',
      });
    }
  },

  create: async (payload) => {
    const reminder = await apiCreate(payload);
    // Insert in due_at order for a tidy list.
    const next = [...get().items, reminder].sort((a, b) =>
      a.due_at.localeCompare(b.due_at),
    );
    set({ items: next });
    return reminder;
  },

  remove: async (id) => {
    await apiDelete(id);
    set({ items: get().items.filter((r) => r.id !== id) });
  },
}));
