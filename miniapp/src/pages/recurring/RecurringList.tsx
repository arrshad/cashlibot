import { useEffect } from 'react';
import { Icon } from '@/components/Icon';
import { formatMoney } from '@/format';
import { t } from '@/i18n';
import { useAppStore } from '@/store/app';
import { useNavStore } from '@/store/nav';
import { useRecurringStore } from '@/store/recurring';
import { getCurrencyOrFallback } from '@/util/currency';

export function RecurringList() {
  const me = useAppStore((s) => s.me!);
  const config = useAppStore((s) => s.config!);
  const categories = useAppStore((s) => s.categories);
  const lang = me.language_code;
  const { items, loading, error, load, remove } = useRecurringStore();
  const go = useNavStore((s) => s.go);

  useEffect(() => {
    load();
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
          <h2 className="step-title">{t(lang, 'recurring.list.title')}</h2>
          <button
            className="text-btn"
            style={{ marginInlineStart: 'auto' }}
            onClick={() => go({ name: 'add-recurring' })}
          >
            <Icon name="fa-plus" /> {t(lang, 'common.add')}
          </button>
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
            <span className="hint-text">{t(lang, 'recurring.list.empty')}</span>
          </div>
        )}

        <div className="reminder-list">
          {items.map((r) => {
            const category = categories.find((c) => c.id === r.category_id);
            const currency = getCurrencyOrFallback(config.currencies, r.currency);
            return (
              <div key={r.id} className="glass-card reminder-card">
                <div className="reminder-card-body">
                  <div className="reminder-card-title">
                    <Icon name={category?.icon ?? 'fa-repeat'} /> {r.description}
                  </div>
                  <div className="reminder-card-meta">
                    <span>{formatMoney(r.amount, currency)}</span>
                    <span>·</span>
                    <span>{t(lang, `recurring.frequency.${r.frequency}`)}</span>
                    <span>·</span>
                    <span>
                      {t(lang, 'recurring.next_due')} {r.next_due_date}
                    </span>
                  </div>
                </div>
                <button
                  className="text-btn text-btn-danger"
                  onClick={() => remove(r.id)}
                >
                  {t(lang, 'common.remove')}
                </button>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
