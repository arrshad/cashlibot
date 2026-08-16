import { useEffect, useMemo, useState } from 'react';
import { Icon } from '@/components/Icon';
import { t } from '@/i18n';
import { useAppStore } from '@/store/app';
import { useDashboardStore } from '@/store/dashboard';
import { useNavStore } from '@/store/nav';
import { pickGreeting } from '@/util/greeting';
import type { Account } from '@/types';
import { AccountCard } from './dashboard/AccountCard';
import { AccountEditSheet } from './dashboard/AccountEditSheet';
import { TransactionRow } from './transactions/TransactionRow';

export function Dashboard() {
  const me = useAppStore((s) => s.me!);
  const config = useAppStore((s) => s.config!);
  const categories = useAppStore((s) => s.categories);
  const lang = me.language_code;

  const { accounts, summary, loading, error, load } = useDashboardStore();
  const go = useNavStore((s) => s.go);

  const [editing, setEditing] = useState<Account | null>(null);

  useEffect(() => {
    if (!summary) load();
  }, [summary, load]);

  const greeting = useMemo(() => pickGreeting(lang), [lang]);
  const recentTx = summary?.recent_transactions ?? [];

  return (
    <div className="app-shell has-tabbar">
      <div className="app-frame">

        <div className="home-top">
          <span className="home-greet-line">
            {greeting}, {me.display_name}
          </span>
          <button
            className="credit-chip"
            onClick={() => go({ name: 'credits' })}
            aria-label={t(lang, 'dashboard.credits_cta')}
          >
            <Icon name="fa-coins" />
            <span>{me.credit_balance.toLocaleString()}</span>
          </button>
        </div>

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


        <section className="section">
          <div className="section-header">
            <h3 className="section-title">{t(lang, 'dashboard.accounts.title')}</h3>
          </div>
          {loading && accounts.length === 0 ? (
            <div className="glass-card" style={{ padding: 16 }}>
              {t(lang, 'common.loading')}
            </div>
          ) : (
            <div className="acct-carousel">
              {accounts.map((a) => (
                <AccountCard
                  key={a.id}
                  account={a}
                  currencies={config.currencies}
                  lang={lang}
                  onEdit={setEditing}
                />
              ))}
              <button
                className="acct-card-empty"
                onClick={() => go({ name: 'add-account' })}
                aria-label={t(lang, 'dashboard.accounts.add_card')}
              >
                <span className="acct-card-empty-plus">
                  <Icon name="fa-plus" />
                </span>
                <span>{t(lang, 'dashboard.accounts.add_card')}</span>
              </button>
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
            <div className="glass-card tx-group-card" style={{ padding: '4px 0' }}>
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

      {editing && (
        <AccountEditSheet
          account={editing}
          lang={lang}
          onClose={() => setEditing(null)}
        />
      )}
    </div>
  );
}
