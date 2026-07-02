import { create } from 'zustand';
import {
  acceptFriend as apiAccept,
  declineFriend as apiDecline,
  fetchFriends,
  sendFriendRequest,
} from '@/api/client';
import { useAppStore } from '@/store/app';
import type { FriendsOverview } from '@/types';

type FriendsStore = {
  overview: FriendsOverview | null;
  loading: boolean;
  error: string | null;
  load: () => Promise<void>;
  request: (username: string) => Promise<void>;
  accept: (id: string) => Promise<void>;
  decline: (id: string) => Promise<void>;
};

export const useFriendsStore = create<FriendsStore>((set, get) => ({
  overview: null,
  loading: false,
  error: null,

  load: async () => {
    set({ loading: true, error: null });
    try {
      const overview = await fetchFriends();
      set({ overview, loading: false });
    } catch (err) {
      set({
        loading: false,
        error: err instanceof Error ? err.message : 'failed to load',
      });
    }
  },

  request: async (username) => {
    await sendFriendRequest(username);
    await get().load();
  },

  accept: async (id) => {
    await apiAccept(id);
    await get().load();
    // Accept grants credits to both users — pull /api/me so the balance chip
    // updates.
    await useAppStore.getState().refreshMe();
  },

  decline: async (id) => {
    await apiDecline(id);
    await get().load();
  },
}));
