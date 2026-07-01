import { Icon } from '@/components/Icon';
import { formatMoney } from '@/format';
import { t } from '@/i18n';
import { useAppStore } from '@/store/app';
import { getCurrencyOrFallback } from '@/util/currency';
import type { Lang, SavingsGoal } from '@/types';

type Props = {
  goal: SavingsGoal;
  lang: Lang;
  onContribute?: () => void;
  onDelete?: () => void;
};

export function GoalCard({ goal, lang, onContribute, onDelete }: Props) {
  const config = useAppStore((s) => s.config!);
  const currency = getCurrencyOrFallback(config.currencies, goal.currency);
  const target = Number(goal.target_amount);
  const current = Number(goal.current_amount);
  const ratio = target > 0 ? Math.min(current / target, 1) : 0;
  const pctText = `${Math.round(ratio * 100)}%`;

  return (
    <div className="glass-card goal-card">
      <div className="goal-card-header">
        <div className="goal-card-title">
          <Icon name={goal.icon} />
          <span>{goal.name}</span>
        </div>
        {goal.is_completed && (
          <span className="chip">{t(lang, 'goal.chip.completed')}</span>
        )}
      </div>

      <div className="goal-card-progress">
        <div className="goal-card-progress-bar">
          <div
            className="goal-card-progress-fill"
            style={{ width: `${ratio * 100}%` }}
          />
        </div>
        <span className="goal-card-progress-label">{pctText}</span>
      </div>

      <div className="goal-card-footer">
        <span>
          {formatMoney(goal.current_amount, currency)} /{' '}
          {formatMoney(goal.target_amount, currency)}
        </span>
        <div style={{ display: 'flex', gap: 6 }}>
          {onContribute && !goal.is_completed && (
            <button className="text-btn" onClick={onContribute}>
              <Icon name="fa-plus" /> {t(lang, 'goal.contribute')}
            </button>
          )}
          {onDelete && (
            <button className="text-btn text-btn-danger" onClick={onDelete}>
              {t(lang, 'common.remove')}
            </button>
          )}
        </div>
      </div>

      {goal.deadline && (
        <span className="hint-text">
          {t(lang, 'goal.deadline_label')}: {goal.deadline}
        </span>
      )}
    </div>
  );
}
