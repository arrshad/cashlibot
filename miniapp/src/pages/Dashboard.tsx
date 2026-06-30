import { t } from '@/i18n';
import { useAppStore } from '@/store/app';

export function Dashboard() {
  const me = useAppStore((s) => s.me);
  const lang = me?.language_code ?? 'en';

  return (
    <div className="app-shell">
      <div className="app-frame">
        <div className="glass-card" style={{ padding: 24 }}>
          <h2 className="hero-title">{t(lang, 'dashboard.placeholder.title')}</h2>
          <p style={{ color: 'var(--text-secondary)', marginTop: 12 }}>
            {t(lang, 'dashboard.placeholder.body')}
          </p>
        </div>
      </div>
    </div>
  );
}
