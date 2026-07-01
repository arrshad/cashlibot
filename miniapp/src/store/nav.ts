import { create } from 'zustand';

export type Route =
  | { name: 'dashboard' }
  | { name: 'transactions' }
  | { name: 'add-tx' }
  | { name: 'add-account' };

type NavStore = {
  route: Route;
  go: (route: Route) => void;
};

export const useNavStore = create<NavStore>((set) => ({
  route: { name: 'dashboard' },
  go: (route) => set({ route }),
}));
