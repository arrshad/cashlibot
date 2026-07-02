import { create } from 'zustand';
import { fetchReportSummary } from '@/api/client';
import type { ReportPeriod, ReportSummary } from '@/types';

type ReportsStore = {
  summary: ReportSummary | null;
  period: ReportPeriod;
  loading: boolean;
  error: string | null;
  load: (period?: ReportPeriod) => Promise<void>;
};

export const useReportsStore = create<ReportsStore>((set, get) => ({
  summary: null,
  period: 'month',
  loading: false,
  error: null,

  load: async (period) => {
    const activePeriod = period ?? get().period;
    set({ loading: true, error: null, period: activePeriod });
    try {
      const summary = await fetchReportSummary(activePeriod);
      set({ summary, loading: false });
    } catch (err) {
      set({
        loading: false,
        error: err instanceof Error ? err.message : 'failed to load',
      });
    }
  },
}));
