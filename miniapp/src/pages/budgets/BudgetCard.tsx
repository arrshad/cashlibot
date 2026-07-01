import { Icon } from '@/components/Icon';
import { formatMoney } from '@/format';
import { t } from '@/i18n';
import { useAppStore } from '@/store/app';
import { getCurrencyOrFallback } from '@/util/currency';
import type { Budget, Lang } from '@/types';

type Props = {
  budget: Budget;
  lang: Lang;
  onDelete?: () => void;
};

function bandColor(ratio: number): string {
  if (ratio >= 1) return 'var(--accent-danger)';
  if (ratio >= 0.9) return 'var(--accent-danger)';
  if (ratio >= 0.75) return 'var(--accent-warning)';
  return 'var(--accent-success)';
}

export function BudgetCard({ budget, lang, onDelete }: Props) {
  const categories = useAppStore((s) => s.categories);
  const config = useAppStore((s) => s.config!);
  const category = categories.find((c) => c.id === budget.category_id);
  const currency = getCurrencyOrFallback(config.currencies, budget.currency);
  const ratio = Math.max(0, budget.ratio);
  const pctText = `${Math.round(ratio * 100)}%`;
  const clampedWidth = Math.min(100, ratio * 100);
  const color = bandColor(ratio);

  return (
    <div className="glass-card budget-card">
      <div className="budget-card-header">
        <div className="budget-card-title">
          <Icon name={category?.icon ?? 'fa-tag'} />
          <span>{category?.name ?? t(lang, 'budget.unknown_category')}</span>
        </div>
        <span className="budget-card-period">
          {t(lang, `budget.period.${budget.period}`)}
        </span>
      </div>

      <div className="budget-card-progress">
        <div className="budget-card-progress-bar">
          <div
            className="budget-card-progress-fill"
            style={{ width: `${clampedWidth}%`, background: color }}
          />
        </div>
        <span className="budget-card-progress-label" style={{ color }}>
          {pctText}
        </span>
      </div>

      <div className="budget-card-footer">
        <span>
          {formatMoney(budget.spent, currency)} / {formatMoney(budget.amount, currency)}
        </span>
        {onDelete && (
          <button className="text-btn text-btn-danger" onClick={onDelete}>
            {t(lang, 'common.remove')}
          </button>
        )}
      </div>
    </div>
  );
}
