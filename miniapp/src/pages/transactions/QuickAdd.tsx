import { useMemo, useState } from 'react';
import { Icon } from '@/components/Icon';
import { t } from '@/i18n';
import { useAppStore } from '@/store/app';
import { useDashboardStore } from '@/store/dashboard';
import { useNavStore } from '@/store/nav';
import { useTransactionsStore } from '@/store/transactions';
import type { TransactionType } from '@/types';

const TYPES: TransactionType[] = ['expense', 'income', 'transfer'];

export function QuickAdd() {
  const me = useAppStore((s) => s.me!);
  const categories = useAppStore((s) => s.categories);
  const accounts = useDashboardStore((s) => s.accounts);
  const create = useTransactionsStore((s) => s.create);
  const go = useNavStore((s) => s.go);
  const lang = me.language_code;

  const [type, setType] = useState<TransactionType>('expense');
  const [amount, setAmount] = useState('');
  const activeAccounts = useMemo(
    () => accounts.filter((a) => !a.is_archived),
    [accounts],
  );
  const [accountId, setAccountId] = useState<string>(
    () => activeAccounts.find((a) => a.is_default)?.id ?? activeAccounts[0]?.id ?? '',
  );
  const [toAccountId, setToAccountId] = useState<string>(
    () => activeAccounts.find((a) => a.id !== accountId)?.id ?? '',
  );
  const [categoryId, setCategoryId] = useState<string>('');
  const [merchant, setMerchant] = useState('');
  const [description, setDescription] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const relevantCategories = useMemo(
    () => categories.filter((c) => (type === 'income' ? c.type === 'income' : c.type === 'expense')),
    [categories, type],
  );

  const numericAmount = Number(amount);
  const canSubmit =
    !submitting &&
    accountId !== '' &&
    Number.isFinite(numericAmount) &&
    numericAmount > 0 &&
    (type !== 'transfer' || (toAccountId !== '' && toAccountId !== accountId));

  const submit = async () => {
    setSubmitting(true);
    setError(null);
    try {
      await create({
        type,
        account_id: accountId,
        amount: amount.trim(),
        occurred_at: new Date().toISOString(),
        to_account_id: type === 'transfer' ? toAccountId : null,
        category_id: type === 'transfer' ? null : categoryId || null,
        merchant: merchant.trim() || null,
        description: description.trim() || null,
      });
      go({ name: 'dashboard' });
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
                onClick={() => go({ name: 'dashboard' })}
                aria-label={t(lang, 'common.back')}
              >
                <Icon name="fa-arrow-left" />
              </button>
              <h2 className="step-title">{t(lang, 'tx.add.title')}</h2>
            </div>

            <div className="type-toggle">
              {TYPES.map((v) => (
                <button
                  key={v}
                  className={`type-toggle-btn ${type === v ? 'type-toggle-btn-active' : ''}`}
                  onClick={() => setType(v)}
                >
                  {t(lang, `tx.type.${v}`)}
                </button>
              ))}
            </div>

            <div className="field">
              <span className="field-label">{t(lang, 'tx.add.amount_label')}</span>
              <input
                className="input input-amount"
                inputMode="decimal"
                placeholder="0"
                value={amount}
                onChange={(e) => setAmount(e.target.value.replace(',', '.'))}
                autoFocus
              />
            </div>

            <div className="field">
              <span className="field-label">
                {type === 'transfer'
                  ? t(lang, 'tx.add.from_account_label')
                  : t(lang, 'tx.add.account_label')}
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

            {type === 'transfer' && (
              <div className="field">
                <span className="field-label">{t(lang, 'tx.add.to_account_label')}</span>
                <div className="choice-grid">
                  {activeAccounts
                    .filter((a) => a.id !== accountId)
                    .map((a) => (
                      <button
                        key={a.id}
                        className={`btn ${toAccountId === a.id ? 'btn-selected' : ''}`}
                        onClick={() => setToAccountId(a.id)}
                      >
                        <Icon name={a.icon} />
                        <span style={{ marginInlineStart: 8 }}>{a.name}</span>
                      </button>
                    ))}
                </div>
              </div>
            )}

            {type !== 'transfer' && (
              <div className="field">
                <span className="field-label">{t(lang, 'tx.add.category_label')}</span>
                <div className="choice-grid">
                  {relevantCategories.map((c) => (
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
            )}

            {type !== 'transfer' && (
              <div className="field">
                <span className="field-label">{t(lang, 'tx.add.merchant_label')}</span>
                <input
                  className="input"
                  value={merchant}
                  onChange={(e) => setMerchant(e.target.value)}
                  placeholder={t(lang, 'tx.add.merchant_placeholder')}
                  maxLength={128}
                />
              </div>
            )}

            <div className="field">
              <span className="field-label">{t(lang, 'tx.add.description_label')}</span>
              <input
                className="input"
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                maxLength={500}
              />
            </div>

            {error && <span className="error-text">{error}</span>}

            <div className="step-footer">
              <button className="btn btn-ghost" onClick={() => go({ name: 'dashboard' })}>
                {t(lang, 'common.back')}
              </button>
              <button
                className="btn btn-primary"
                disabled={!canSubmit}
                onClick={submit}
              >
                {t(lang, 'tx.add.submit')}
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
