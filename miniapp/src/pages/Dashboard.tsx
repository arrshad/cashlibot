import { useEffect, useState } from 'react';
import { Icon } from '@/components/Icon';
import { t } from '@/i18n';
import { useAppStore } from '@/store/app';
import { useDashboardStore } from '@/store/dashboard';
import { AccountCard } from './dashboard/AccountCard';
import { AddAccount } from './dashboard/AddAccount';
import { TotalsRow } from './dashboard/TotalsRow';

export function Dashboard() {
  const me = useAppStore((s) => s.me!);
  const config = useAppStore((s) => s.config!);
  const lang = me.language_code;

  const { accounts, summary, loading, error, load } = useDashboardStore();
  const [view, setView] = useState<'main' | 'add'>('main');

  useEffect(() => {
    if (!summary) load();
  }, [summary, load]);

  if (view === 'add') {
    return <AddAccount lang={lang} onDone={() => setView('main')} />;
  }

  return (
    <div className="app-shell">
      <div className="app-frame">
        <header className="dashboard-greeting">
          <span className="hint-text">
            {t(lang, 'dashboard.greeting.eyebrow')}
          </span>
          <h1 className="hero-title">{me.display_name}</h1>
        </header>

        {error && (
          <div className="glass-card" style={{ padding: 16 }}>
            <span className="error-text">{error}</span>
            <button
              className="btn btn-ghost"
              style={{ marginTop: 8 }}
              onClick={() => load()}
            >
              {t(lang, 'common.retry')}
            </button>
          </div>
        )}

        {summary && (
          <TotalsRow
            totals={summary.totals_by_currency}
            currencies={config.currencies}
            defaultCurrency={summary.default_currency}
            lang={lang}
          />
        )}

        <section className="section">
          <div className="section-header">
            <h3 className="section-title">{t(lang, 'dashboard.accounts.title')}</h3>
            <button className="text-btn" onClick={() => setView('add')}>
              <Icon name="fa-plus" /> {t(lang, 'dashboard.accounts.add')}
            </button>
          </div>

          {loading && accounts.length === 0 ? (
            <div className="glass-card" style={{ padding: 16 }}>
              {t(lang, 'common.loading')}
            </div>
          ) : accounts.length === 0 ? (
            <div className="glass-card" style={{ padding: 16 }}>
              <span className="hint-text">
                {t(lang, 'dashboard.accounts.empty')}
              </span>
            </div>
          ) : (
            <div className="account-list">
              {accounts.map((a) => (
                <AccountCard
                  key={a.id}
                  account={a}
                  currencies={config.currencies}
                  lang={lang}
                />
              ))}
            </div>
          )}
        </section>

        <p className="hint-text center" style={{ marginTop: 12 }}>
          {t(lang, 'dashboard.transactions.hint')}
        </p>
      </div>
    </div>
  );
}
