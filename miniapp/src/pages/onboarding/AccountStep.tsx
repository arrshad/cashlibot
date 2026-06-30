import { useState } from 'react';
import { t } from '@/i18n';
import { StepShell } from './StepShell';
import type {
  AccountType,
  AccountTypeOption,
  CurrencyOption,
  Lang,
} from '@/types';

type Props = {
  lang: Lang;
  step: number;
  total: number;
  initialCurrency: string;
  currencies: CurrencyOption[];
  accountTypes: AccountTypeOption[];
  onSubmit: (a: { name: string; type: AccountType; currency: string }) => void;
  onBack: () => void;
  submitting?: boolean;
};

export function AccountStep({
  lang,
  step,
  total,
  initialCurrency,
  currencies,
  accountTypes,
  onSubmit,
  onBack,
  submitting,
}: Props) {
  const [name, setName] = useState('');
  const [type, setType] = useState<AccountType>('cash');
  const [currency, setCurrency] = useState(initialCurrency);

  const canSubmit = name.trim().length > 0 && name.trim().length <= 40 && !submitting;

  return (
    <StepShell
      lang={lang}
      step={step}
      total={total}
      title={t(lang, 'onboarding.account.title')}
      canBack
      onBack={onBack}
      primaryLabel={t(lang, 'onboarding.account.submit')}
      primaryDisabled={!canSubmit}
      onPrimary={() =>
        onSubmit({ name: name.trim(), type, currency })
      }
    >
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
        />
      </div>

      <div className="field">
        <span className="field-label">
          {t(lang, 'onboarding.account.type_label')}
        </span>
        <div className="choice-grid">
          {accountTypes.map((at) => (
            <button
              key={at.value}
              className={`btn ${type === at.value ? 'btn-selected' : ''}`}
              onClick={() => setType(at.value)}
            >
              {t(lang, `onboarding.account.type.${at.value}`)}
            </button>
          ))}
        </div>
      </div>

      <div className="field">
        <span className="field-label">
          {t(lang, 'onboarding.account.currency_label')}
        </span>
        <div className="choice-grid">
          {currencies.map((c) => (
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
    </StepShell>
  );
}
