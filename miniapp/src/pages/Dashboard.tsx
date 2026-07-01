import { useEffect } from 'react';
import { Icon } from '@/components/Icon';
import { t } from '@/i18n';
import { useAppStore } from '@/store/app';
import { useDashboardStore } from '@/store/dashboard';
import { useNavStore } from '@/store/nav';
import { AccountCard } from './dashboard/AccountCard';
import { TotalsRow } from './dashboard/TotalsRow';
import { TransactionRow } from './transactions/TransactionRow';

export function Dashboard() {
  const me = useAppStore((s) => s.me!);
  const config = useAppStore((s) => s.config!);
  const categories = useAppStore((s) => s.categories);
  const lang = me.language_code;

  const { accounts, summary, loading, error, load } = useDashboardStore();
  const go = useNavStore((s) => s.go);

  useEffect(() => {
    if (!summary) load();
  }, [summary, load]);

  const recentTx = summary?.recent_transactions ?? [];

  return (
    <div className="app-shell">
      <div className="app-frame">
        <header className="dashboard-greeting">
          <span className="hint-text">{t(lang, 'dashboard.greeting.eyebrow')}</span>
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

        <div className="dashboard-actions">
          <button
            className="btn btn-primary quick-add-cta"
            onClick={() => go({ name: 'add-tx' })}
          >
            <Icon name="fa-plus" /> {t(lang, 'dashboard.add_tx_cta')}
          </button>
          <button
            className="btn btn-ghost"
            onClick={() => go({ name: 'budgets' })}
          >
            {t(lang, 'dashboard.budgets_cta')}
          </button>
        </div>

        <section className="section">
          <div className="section-header">
            <h3 className="section-title">{t(lang, 'dashboard.accounts.title')}</h3>
            <button className="text-btn" onClick={() => go({ name: 'add-account' })}>
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

        <section className="section">
          <div className="section-header">
            <h3 className="section-title">{t(lang, 'dashboard.recent.title')}</h3>
            {recentTx.length > 0 && (
              <button
                className="text-btn"
                onClick={() => go({ name: 'transactions' })}
              >
                {t(lang, 'dashboard.recent.see_all')}
              </button>
            )}
          </div>

          {recentTx.length === 0 ? (
            <div className="glass-card" style={{ padding: 16 }}>
              <span className="hint-text">{t(lang, 'dashboard.recent.empty')}</span>
            </div>
          ) : (
            <div className="tx-list">
              {recentTx.map((tx) => (
                <TransactionRow
                  key={tx.id}
                  tx={tx}
                  accounts={accounts}
                  categories={categories}
                />
              ))}
            </div>
          )}
        </section>
      </div>
    </div>
  );
}
