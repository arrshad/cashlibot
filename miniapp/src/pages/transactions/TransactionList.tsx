import { useEffect } from 'react';
import { Icon } from '@/components/Icon';
import { t } from '@/i18n';
import { useAppStore } from '@/store/app';
import { useDashboardStore } from '@/store/dashboard';
import { useNavStore } from '@/store/nav';
import { useTransactionsStore } from '@/store/transactions';
import { TransactionRow } from './TransactionRow';

export function TransactionList() {
  const me = useAppStore((s) => s.me!);
  const categories = useAppStore((s) => s.categories);
  const accounts = useDashboardStore((s) => s.accounts);
  const { items, loading, error, load } = useTransactionsStore();
  const go = useNavStore((s) => s.go);
  const lang = me.language_code;

  useEffect(() => {
    load({ limit: 100 });
  }, [load]);

  return (
    <div className="app-shell">
      <div className="app-frame">
        <div className="page-header">
          <button
            className="icon-btn"
            onClick={() => go({ name: 'dashboard' })}
            aria-label={t(lang, 'common.back')}
          >
            <Icon name="fa-arrow-left" />
          </button>
          <h2 className="step-title">{t(lang, 'tx.list.title')}</h2>
        </div>

        {error && (
          <div className="glass-card" style={{ padding: 16 }}>
            <span className="error-text">{error}</span>
          </div>
        )}

        {loading && items.length === 0 && (
          <div className="glass-card" style={{ padding: 16 }}>
            {t(lang, 'common.loading')}
          </div>
        )}

        {!loading && items.length === 0 && (
          <div className="glass-card" style={{ padding: 16 }}>
            <span className="hint-text">{t(lang, 'tx.list.empty')}</span>
          </div>
        )}

        <div className="tx-list">
          {items.map((tx) => (
            <TransactionRow
              key={tx.id}
              tx={tx}
              accounts={accounts}
              categories={categories}
            />
          ))}
        </div>
      </div>
    </div>
  );
}
