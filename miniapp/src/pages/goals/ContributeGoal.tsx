import { useState } from 'react';
import { Sheet } from '@/components/Sheet';
import { formatMoney } from '@/format';
import { t } from '@/i18n';
import { useAppStore } from '@/store/app';
import { useGoalsStore } from '@/store/goals';
import { useNavStore } from '@/store/nav';
import { getCurrencyOrFallback } from '@/util/currency';

type Props = {
  goalId: string;
};

export function ContributeGoal({ goalId }: Props) {
  const me = useAppStore((s) => s.me!);
  const config = useAppStore((s) => s.config!);
  const goals = useGoalsStore((s) => s.items);
  const contribute = useGoalsStore((s) => s.contribute);
  const go = useNavStore((s) => s.go);
  const lang = me.language_code;

  const goal = goals.find((g) => g.id === goalId);
  const [amount, setAmount] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [justCompleted, setJustCompleted] = useState(false);

  if (!goal) {
    return (
      <Sheet
        title={t(lang, 'goal.contribute_title')}
        onClose={() => go({ name: 'goals' })}
      >
        <p className="error-text">{t(lang, 'goal.contribute_missing')}</p>
      </Sheet>
    );
  }

  const currency = getCurrencyOrFallback(config.currencies, goal.currency);
  const numeric = Number(amount);
  const canSubmit = !submitting && Number.isFinite(numeric) && numeric > 0;

  const submit = async () => {
    setSubmitting(true);
    setError(null);
    try {
      const result = await contribute(goalId, amount.trim());
      if (result.just_completed) {
        setJustCompleted(true);
      } else {
        go({ name: 'goals' });
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'failed');
    } finally {
      setSubmitting(false);
    }
  };

  if (justCompleted) {
    return (
      <Sheet
        title={t(lang, 'goal.completed_title')}
        onClose={() => go({ name: 'goals' })}
      >
        <p style={{ color: 'var(--text-secondary)', textAlign: 'center' }}>
          {t(lang, 'goal.completed_body', { name: goal.name })}
        </p>
        <button
          className="btn btn-primary"
          onClick={() => go({ name: 'goals' })}
        >
          {t(lang, 'common.done')}
        </button>
      </Sheet>
    );
  }

  return (
    <Sheet
      title={t(lang, 'goal.contribute_title')}
      onClose={() => go({ name: 'goals' })}
      footer={
        <button
          className="btn btn-primary"
          disabled={!canSubmit}
          onClick={submit}
        >
          {t(lang, 'goal.contribute_submit')}
        </button>
      }
    >
      <p className="hint-text">
        {goal.name} · {formatMoney(goal.current_amount, currency)} /{' '}
        {formatMoney(goal.target_amount, currency)}
      </p>

      <div className="field">
        <span className="field-label">
          {t(lang, 'goal.contribute_amount_label')}
        </span>
        <input
          className="input input-amount"
          inputMode="decimal"
          value={amount}
          onChange={(e) => setAmount(e.target.value.replace(',', '.'))}
          placeholder="0"
          autoFocus
        />
      </div>

      {error && <span className="error-text">{error}</span>}
    </Sheet>
  );
}
