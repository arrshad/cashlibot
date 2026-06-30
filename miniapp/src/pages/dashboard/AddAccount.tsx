import { useState } from 'react';
import { Icon } from '@/components/Icon';
import { t } from '@/i18n';
import { useAppStore } from '@/store/app';
import { useDashboardStore } from '@/store/dashboard';
import type { AccountType, Lang } from '@/types';

type Props = {
  lang: Lang;
  onDone: () => void;
};

export function AddAccount({ lang, onDone }: Props) {
  const me = useAppStore((s) => s.me!);
  const config = useAppStore((s) => s.config!);
  const create = useDashboardStore((s) => s.createAccount);

  const [name, setName] = useState('');
  const [type, setType] = useState<AccountType>('cash');
  const [currency, setCurrency] = useState(me.default_currency ?? 'USD');
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const canSubmit = name.trim().length > 0 && !submitting;

  const submit = async () => {
    setSubmitting(true);
    setError(null);
    try {
      await create({ name: name.trim(), type, currency });
      onDone();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'failed to create');
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
              <button className="icon-btn" onClick={onDone} aria-label="Back">
                <Icon name="fa-arrow-left" />
              </button>
              <h2 className="step-title">{t(lang, 'dashboard.add_account.title')}</h2>
            </div>

            <div className="field">
              <span className="field-label">
                {t(lang, 'onboarding.account.name_label')}
              </span>
              <input
                className="input"
                placeholder={t(lang, 'onboarding.account.name_placeholder')}
                value={name}
                onChange={(e) => setName(e.target.value)}
                maxLength={40}
                autoFocus
              />
            </div>

            <div className="field">
              <span className="field-label">
                {t(lang, 'onboarding.account.type_label')}
              </span>
              <div className="choice-grid">
                {config.account_types.map((at) => (
                  <button
                    key={at.value}
                    className={`btn ${type === at.value ? 'btn-selected' : ''}`}
                    onClick={() => setType(at.value)}
                  >
                    <Icon name={at.icon} />
                    <span style={{ marginInlineStart: 8 }}>
                      {t(lang, `onboarding.account.type.${at.value}`)}
                    </span>
                  </button>
                ))}
              </div>
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

            {error && <span className="error-text">{error}</span>}

            <div className="step-footer">
              <button className="btn btn-ghost" onClick={onDone}>
                {t(lang, 'common.back')}
              </button>
              <button
                className="btn btn-primary"
                disabled={!canSubmit}
                onClick={submit}
              >
                {t(lang, 'dashboard.add_account.submit')}
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
