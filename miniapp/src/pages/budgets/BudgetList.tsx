import { useEffect } from 'react';
import { Icon } from '@/components/Icon';
import { t } from '@/i18n';
import { useAppStore } from '@/store/app';
import { useBudgetsStore } from '@/store/budgets';
import { useNavStore } from '@/store/nav';
import { BudgetCard } from './BudgetCard';

export function BudgetList() {
  const me = useAppStore((s) => s.me!);
  const lang = me.language_code;
  const { items, loading, error, load, remove } = useBudgetsStore();
  const go = useNavStore((s) => s.go);

  useEffect(() => {
    load();
  }, [load]);

  return (
    <div className="app-shell has-tabbar">
      <div className="app-frame">
        <div className="page-header">
          <h2 className="step-title">{t(lang, 'budget.list.title')}</h2>
          <button
            className="text-btn"
            style={{ marginInlineStart: 'auto' }}
            onClick={() => go({ name: 'add-budget' })}
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
            <span className="hint-text">{t(lang, 'budget.list.empty')}</span>
          </div>
        )}

        <div className="budget-list">
          {items.map((b) => (
            <BudgetCard
              key={b.id}
              budget={b}
              lang={lang}
              onDelete={() => remove(b.id)}
            />
          ))}
        </div>
      </div>
    </div>
  );
}
