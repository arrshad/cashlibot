import { create } from 'zustand';
import { fetchConfig, fetchMe } from '@/api/client';
import { applyHtmlLang } from '@/i18n';
import type { AppConfig, Me } from '@/types';

type AppStore = {
  me: Me | null;
  config: AppConfig | null;
  loading: boolean;
  error: string | null;
  load: () => Promise<void>;
  setMe: (me: Me) => void;
};

export const useAppStore = create<AppStore>((set) => ({
  me: null,
  config: null,
  loading: true,
  error: null,
  setMe: (me) => {
    applyHtmlLang(me.language_code);
    set({ me });
  },
  load: async () => {
    set({ loading: true, error: null });
    try {
      const [me, config] = await Promise.all([fetchMe(), fetchConfig()]);
      applyHtmlLang(me.language_code);
      set({ me, config, loading: false });
    } catch (err) {
      const message =
        err instanceof Error ? err.message : 'failed to load';
      set({ loading: false, error: message });
    }
  },
}));
