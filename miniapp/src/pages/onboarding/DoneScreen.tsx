import { t } from '@/i18n';
import { getTelegramWebApp } from '@/telegram';
import type { Lang } from '@/types';

type Props = {
  lang: Lang;
  credits: number;
};

export function DoneScreen({ lang, credits }: Props) {
  return (
    <div className="app-shell">
      <div className="app-frame">
        <div className="glass-card" style={{ padding: 28, textAlign: 'center' }}>
          <h2 className="hero-title">{t(lang, 'onboarding.done.title')}</h2>
          <p style={{ color: 'var(--text-secondary)', marginTop: 16 }}>
            {t(lang, 'onboarding.done.subtitle', { credits })}
          </p>
          <button
            className="btn btn-primary"
            style={{ marginTop: 24 }}
            onClick={() => getTelegramWebApp()?.close()}
          >
            {t(lang, 'onboarding.done.close')}
          </button>
        </div>
      </div>
    </div>
  );
}
