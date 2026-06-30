import { useEffect } from 'react';
import { Dashboard } from '@/pages/Dashboard';
import { ErrorView } from '@/pages/ErrorView';
import { Loading } from '@/pages/Loading';
import { Onboarding } from '@/pages/onboarding';
import { Outside } from '@/pages/Outside';
import { useAppStore } from '@/store/app';
import { getInitDataRaw, notifyReady } from '@/telegram';

export default function App() {
  const { me, config, loading, error, load } = useAppStore();
  const initData = getInitDataRaw();

  useEffect(() => {
    notifyReady();
    if (initData) {
      load();
    }
  }, [initData, load]);

  if (!initData) return <Outside />;
  if (loading) return <Loading />;
  if (error) return <ErrorView message={error} onRetry={load} />;
  if (!me || !config) return <Loading />;
  if (!me.onboarding_completed) return <Onboarding />;
  return <Dashboard />;
}
