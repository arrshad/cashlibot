import { create } from 'zustand';
import { fetchCategories, fetchConfig, fetchMe } from '@/api/client';
import { applyHtmlLang } from '@/i18n';
import type { AppConfig, Category, Me } from '@/types';

type AppStore = {
  me: Me | null;
  config: AppConfig | null;
  categories: Category[];
  loading: boolean;
  error: string | null;
  load: () => Promise<void>;
  reloadCategories: () => Promise<void>;
  refreshMe: () => Promise<void>;
  setMe: (me: Me) => void;
};

export const useAppStore = create<AppStore>((set) => ({
  me: null,
  config: null,
  categories: [],
  loading: true,
  error: null,
  setMe: (me) => {
    applyHtmlLang(me.language_code);
    set({ me });
  },
  load: async () => {
    set({ loading: true, error: null });
    try {
      const [me, config, categories] = await Promise.all([
        fetchMe(),
        fetchConfig(),
        fetchCategories().catch(() => [] as Category[]),
      ]);
      applyHtmlLang(me.language_code);
      set({ me, config, categories, loading: false });
    } catch (err) {
      const message = err instanceof Error ? err.message : 'failed to load';
      set({ loading: false, error: message });
    }
  },
  reloadCategories: async () => {
    const categories = await fetchCategories();
    set({ categories });
  },
  refreshMe: async () => {
    const me = await fetchMe();
    applyHtmlLang(me.language_code);
    set({ me });
  },
}));
