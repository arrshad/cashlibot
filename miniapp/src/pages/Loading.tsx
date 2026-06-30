import { t } from '@/i18n';
import { useAppStore } from '@/store/app';

export function Loading() {
  const lang = useAppStore((s) => s.me?.language_code ?? 'en');
  return (
    <div className="status-screen">
      <div className="glass-card">
        <p>{t(lang, 'common.loading')}</p>
      </div>
    </div>
  );
}
