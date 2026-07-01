import { useMemo, useState } from 'react';
import { Icon } from '@/components/Icon';
import { t } from '@/i18n';
import { useAppStore } from '@/store/app';
import { useBudgetsStore } from '@/store/budgets';
import { useNavStore } from '@/store/nav';
import type { BudgetPeriod } from '@/types';

const PERIODS: BudgetPeriod[] = ['weekly', 'monthly', 'yearly'];

export function AddBudget() {
  const me = useAppStore((s) => s.me!);
  const categories = useAppStore((s) => s.categories);
  const config = useAppStore((s) => s.config!);
  const create = useBudgetsStore((s) => s.create);
  const go = useNavStore((s) => s.go);
  const lang = me.language_code;

  const expenseCategories = useMemo(
    () => categories.filter((c) => c.type === 'expense'),
    [categories],
  );
  const [categoryId, setCategoryId] = useState<string>(expenseCategories[0]?.id ?? '');
  const [amount, setAmount] = useState('');
  const [period, setPeriod] = useState<BudgetPeriod>('monthly');
  const [currency, setCurrency] = useState(me.default_currency ?? 'USD');
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const numeric = Number(amount);
  const canSubmit =
    !submitting &&
    categoryId !== '' &&
    Number.isFinite(numeric) &&
    numeric > 0;

  const submit = async () => {
    setSubmitting(true);
    setError(null);
    try {
      await create({
        category_id: categoryId,
        amount: amount.trim(),
        currency,
        period,
      });
      go({ name: 'budgets' });
    } catch (err) {
      setError(err instanceof Error ? err.message : 'failed');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="app-shell">
      <div className="app-frame">
        <div className="glass-card" style={{ padding: 22 }}>
          <div className="step">
            <div className="page-header">
              <button
                className="icon-btn"
                onClick={() => go({ name: 'budgets' })}
                aria-label={t(lang, 'common.back')}
              >
                <Icon name="fa-arrow-left" />
              </button>
              <h2 className="step-title">{t(lang, 'budget.add.title')}</h2>
            </div>

            <div className="field">
              <span className="field-label">{t(lang, 'budget.add.category_label')}</span>
              <div className="choice-grid">
                {expenseCategories.map((c) => (
                  <button
                    key={c.id}
                    className={`btn ${categoryId === c.id ? 'btn-selected' : ''}`}
                    onClick={() => setCategoryId(c.id)}
                  >
                    <Icon name={c.icon} />
                    <span style={{ marginInlineStart: 8 }}>{c.name}</span>
                  </button>
                ))}
              </div>
            </div>

            <div className="field">
              <span className="field-label">{t(lang, 'budget.add.amount_label')}</span>
              <input
                className="input input-amount"
                inputMode="decimal"
                value={amount}
                onChange={(e) => setAmount(e.target.value.replace(',', '.'))}
                placeholder="0"
              />
            </div>

            <div className="field">
              <span className="field-label">{t(lang, 'budget.add.period_label')}</span>
              <div className="choice-grid">
                {PERIODS.map((p) => (
                  <button
                    key={p}
                    className={`btn ${period === p ? 'btn-selected' : ''}`}
                    onClick={() => setPeriod(p)}
                  >
                    {t(lang, `budget.period.${p}`)}
                  </button>
                ))}
              </div>
            </div>

            <div className="field">
              <span className="field-label">{t(lang, 'onboarding.account.currency_label')}</span>
              <div className="choice-grid">
                {config.currencies.map((c) => (
                  <button
                    key={c.code}
                    className={`btn ${currency === c.code ? 'btn-selected' : ''}`}
                    onClick={() => setCurrency(c.code)}
                  >
                    <span style={{ fontWeight: 600 }}>{c.code}</span>
                    <span style={{ color: 'var(--text-secondary)', marginInlineStart: 8 }}>
                      {c.symbol}
                    </span>
                  </button>
                ))}
              </div>
            </div>

            {error && <span className="error-text">{error}</span>}

            <div className="step-footer">
              <button className="btn btn-ghost" onClick={() => go({ name: 'budgets' })}>
                {t(lang, 'common.back')}
              </button>
              <button
                className="btn btn-primary"
                disabled={!canSubmit}
                onClick={submit}
              >
                {t(lang, 'budget.add.submit')}
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
