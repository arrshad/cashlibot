import { useState } from 'react';
import { Icon } from '@/components/Icon';
import { t } from '@/i18n';
import { useAppStore } from '@/store/app';
import { useDashboardStore } from '@/store/dashboard';
import { useGoalsStore } from '@/store/goals';
import { useNavStore } from '@/store/nav';

export function AddGoal() {
  const me = useAppStore((s) => s.me!);
  const config = useAppStore((s) => s.config!);
  const accounts = useDashboardStore((s) => s.accounts);
  const create = useGoalsStore((s) => s.create);
  const go = useNavStore((s) => s.go);
  const lang = me.language_code;

  const [name, setName] = useState('');
  const [target, setTarget] = useState('');
  const [currency, setCurrency] = useState(me.default_currency ?? 'USD');
  const [deadline, setDeadline] = useState('');
  const [linkedAccountId, setLinkedAccountId] = useState<string>('');
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const targetNum = Number(target);
  const canSubmit =
    !submitting &&
    name.trim().length > 0 &&
    Number.isFinite(targetNum) &&
    targetNum > 0;

  const submit = async () => {
    setSubmitting(true);
    setError(null);
    try {
      await create({
        name: name.trim(),
        target_amount: target.trim(),
        currency,
        deadline: deadline || null,
        linked_account_id: linkedAccountId || null,
      });
      go({ name: 'goals' });
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
                onClick={() => go({ name: 'goals' })}
                aria-label={t(lang, 'common.back')}
              >
                <Icon name="fa-arrow-left" />
              </button>
              <h2 className="step-title">{t(lang, 'goal.add.title')}</h2>
            </div>

            <div className="field">
              <span className="field-label">{t(lang, 'goal.add.name_label')}</span>
              <input
                className="input"
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder={t(lang, 'goal.add.name_placeholder')}
                maxLength={60}
                autoFocus
              />
            </div>

            <div className="field">
              <span className="field-label">{t(lang, 'goal.add.target_label')}</span>
              <input
                className="input input-amount"
                inputMode="decimal"
                value={target}
                onChange={(e) => setTarget(e.target.value.replace(',', '.'))}
                placeholder="0"
              />
            </div>

            <div className="field">
              <span className="field-label">
                {t(lang, 'onboarding.account.currency_label')}
              </span>
              <div className="choice-grid">
                {config.currencies.map((c) => (
                  <button
                    key={c.code}
                    className={`btn ${currency === c.code ? 'btn-selected' : ''}`}
                    onClick={() => setCurrency(c.code)}
                  >
                    <span style={{ fontWeight: 600 }}>{c.code}</span>
                    <span
                      style={{
                        color: 'var(--text-secondary)',
                        marginInlineStart: 8,
                      }}
                    >
                      {c.symbol}
                    </span>
                  </button>
                ))}
              </div>
            </div>

            <div className="field">
              <span className="field-label">{t(lang, 'goal.add.deadline_label')}</span>
              <input
                className="input"
                type="date"
                value={deadline}
                onChange={(e) => setDeadline(e.target.value)}
              />
            </div>

            {accounts.length > 0 && (
              <div className="field">
                <span className="field-label">
                  {t(lang, 'goal.add.linked_account_label')}
                </span>
                <div className="choice-grid">
                  <button
                    className={`btn ${linkedAccountId === '' ? 'btn-selected' : ''}`}
                    onClick={() => setLinkedAccountId('')}
                  >
                    {t(lang, 'goal.add.no_linked_account')}
                  </button>
                  {accounts
                    .filter((a) => !a.is_archived)
                    .map((a) => (
                      <button
                        key={a.id}
                        className={`btn ${linkedAccountId === a.id ? 'btn-selected' : ''}`}
                        onClick={() => setLinkedAccountId(a.id)}
                      >
                        <Icon name={a.icon} />
                        <span style={{ marginInlineStart: 8 }}>{a.name}</span>
                      </button>
                    ))}
                </div>
              </div>
            )}

            {error && <span className="error-text">{error}</span>}

            <div className="step-footer">
              <button className="btn btn-ghost" onClick={() => go({ name: 'goals' })}>
                {t(lang, 'common.back')}
              </button>
              <button
                className="btn btn-primary"
                disabled={!canSubmit}
                onClick={submit}
              >
                {t(lang, 'goal.add.submit')}
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
