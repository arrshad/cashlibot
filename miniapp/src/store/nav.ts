import { create } from 'zustand';

export type Route =
  | { name: 'dashboard' }
  | { name: 'transactions' }
  | { name: 'add-tx' }
  | { name: 'add-account' }
  | { name: 'budgets' }
  | { name: 'add-budget' };

type NavStore = {
  route: Route;
  go: (route: Route) => void;
};

export const useNavStore = create<NavStore>((set) => ({
  route: { name: 'dashboard' },
  go: (route) => set({ route }),
}));
