import { useMemo, useState } from 'react';
import { Icon } from '@/components/Icon';
import { Sheet } from '@/components/Sheet';
import { t } from '@/i18n';
import { useAppStore } from '@/store/app';
import { useDashboardStore } from '@/store/dashboard';
import { useNavStore } from '@/store/nav';
import { useRecurringStore } from '@/store/recurring';
import type { Frequency } from '@/types';

const FREQUENCIES: Frequency[] = ['daily', 'weekly', 'monthly', 'yearly'];

function tomorrowIso(): string {
  const d = new Date();
  d.setDate(d.getDate() + 1);
  const pad = (n: number) => String(n).padStart(2, '0');
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`;
}

export function AddRecurring() {
  const me = useAppStore((s) => s.me!);
  const categories = useAppStore((s) => s.categories);
  const accounts = useDashboardStore((s) => s.accounts);
  const create = useRecurringStore((s) => s.create);
  const go = useNavStore((s) => s.go);
  const lang = me.language_code;

  const activeAccounts = useMemo(
    () => accounts.filter((a) => !a.is_archived),
    [accounts],
  );

  const [description, setDescription] = useState('');
  const [amount, setAmount] = useState('');
  const [accountId, setAccountId] = useState<string>(
    () =>
      activeAccounts.find((a) => a.is_default)?.id ?? activeAccounts[0]?.id ?? '',
  );
  const [categoryId, setCategoryId] = useState<string>('');
  const [frequency, setFrequency] = useState<Frequency>('monthly');
  const [nextDue, setNextDue] = useState(useMemo(tomorrowIso, []));
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const numeric = Number(amount);
  const canSubmit =
    !submitting &&
    description.trim().length > 0 &&
    accountId !== '' &&
    categoryId !== '' &&
    Number.isFinite(numeric) &&
    numeric > 0 &&
    nextDue !== '';

  const submit = async () => {
    setSubmitting(true);
    setError(null);
    try {
      await create({
        account_id: accountId,
        category_id: categoryId,
        amount: amount.trim(),
        description: description.trim(),
        frequency,
        next_due_date: nextDue,
      });
      go({ name: 'recurring' });
    } catch (err) {
      setError(err instanceof Error ? err.message : 'failed');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <Sheet
      title={t(lang, 'recurring.add.title')}
      onClose={() => go({ name: 'recurring' })}
      footer={
        <button
          className="btn btn-primary"
          disabled={!canSubmit}
          onClick={submit}
        >
          {t(lang, 'recurring.add.submit')}
        </button>
      }
    >
      <div className="field">
        <span className="field-label">
          {t(lang, 'recurring.add.description_label')}
        </span>
        <input
          className="input"
          value={description}
          onChange={(e) => setDescription(e.target.value)}
          placeholder={t(lang, 'recurring.add.description_placeholder')}
          maxLength={200}
          autoFocus
        />
      </div>

      <div className="field">
        <span className="field-label">
          {t(lang, 'recurring.add.amount_label')}
        </span>
        <input
          className="input input-amount"
          inputMode="decimal"
          value={amount}
          onChange={(e) => setAmount(e.target.value.replace(',', '.'))}
          placeholder="0"
        />
      </div>

      <div className="field">
        <span className="field-label">
          {t(lang, 'recurring.add.account_label')}
        </span>
        <div className="choice-grid">
          {activeAccounts.map((a) => (
            <button
              key={a.id}
              className={`btn ${accountId === a.id ? 'btn-selected' : ''}`}
              onClick={() => setAccountId(a.id)}
            >
              <Icon name={a.icon} />
              <span style={{ marginInlineStart: 8 }}>{a.name}</span>
            </button>
          ))}
        </div>
      </div>

      <div className="field">
        <span className="field-label">
          {t(lang, 'recurring.add.category_label')}
        </span>
        <div className="choice-grid">
          {categories.map((c) => (
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
        <span className="field-label">
          {t(lang, 'recurring.add.frequency_label')}
        </span>
        <div className="choice-grid">
          {FREQUENCIES.map((f) => (
            <button
              key={f}
              className={`btn ${frequency === f ? 'btn-selected' : ''}`}
              onClick={() => setFrequency(f)}
            >
              {t(lang, `recurring.frequency.${f}`)}
            </button>
          ))}
        </div>
      </div>

      <div className="field">
        <span className="field-label">
          {t(lang, 'recurring.add.next_due_label')}
        </span>
        <input
          className="input"
          type="date"
          value={nextDue}
          onChange={(e) => setNextDue(e.target.value)}
        />
      </div>

      {error && <span className="error-text">{error}</span>}
    </Sheet>
  );
}
