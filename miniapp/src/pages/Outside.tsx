import { t } from '@/i18n';

export function Outside() {
  return (
    <div className="status-screen">
      <div className="glass-card">
        <h2 className="hero-title">Cashlibot</h2>
        <p style={{ marginTop: 16 }}>{t('en', 'auth.outside_telegram')}</p>
      </div>
    </div>
  );
}
