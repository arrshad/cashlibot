import { useEffect } from 'react';
import { Icon } from '@/components/Icon';
import { t } from '@/i18n';
import { useAppStore } from '@/store/app';
import { useGoalsStore } from '@/store/goals';
import { useNavStore } from '@/store/nav';
import { GoalCard } from './GoalCard';

export function GoalList() {
  const me = useAppStore((s) => s.me!);
  const lang = me.language_code;
  const { items, loading, error, load, remove } = useGoalsStore();
  const go = useNavStore((s) => s.go);

  useEffect(() => {
    load();
  }, [load]);

  return (
    <div className="app-shell has-tabbar">
      <div className="app-frame">
        <div className="page-header">
          <h2 className="step-title">{t(lang, 'goal.list.title')}</h2>
          <button
            className="text-btn"
            style={{ marginInlineStart: 'auto' }}
            onClick={() => go({ name: 'add-goal' })}
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
            <span className="hint-text">{t(lang, 'goal.list.empty')}</span>
          </div>
        )}

        <div className="goal-list">
          {items.map((g) => (
            <GoalCard
              key={g.id}
              goal={g}
              lang={lang}
              onContribute={() =>
                go({ name: 'contribute-goal', goalId: g.id })
              }
              onDelete={() => remove(g.id)}
            />
          ))}
        </div>
      </div>
    </div>
  );
}
