import { t } from '@/i18n';
import { StepShell } from './StepShell';
import type { CurrencyOption, Lang } from '@/types';

type Props = {
  lang: Lang;
  step: number;
  total: number;
  value: string | undefined;
  options: CurrencyOption[];
  onPick: (code: string) => void;
  onBack: () => void;
};

export function CurrencyStep({
  lang,
  step,
  total,
  value,
  options,
  onPick,
  onBack,
}: Props) {
  return (
    <StepShell
      lang={lang}
      step={step}
      total={total}
      title={t(lang, 'onboarding.currency.title')}
      subtitle={t(lang, 'onboarding.currency.subtitle')}
      canBack
      onBack={onBack}
    >
      <div className="choice-grid">
        {options.map((c) => (
          <button
            key={c.code}
            className={`btn ${value === c.code ? 'btn-selected' : ''}`}
            onClick={() => onPick(c.code)}
          >
            <span style={{ fontWeight: 600 }}>{c.code}</span>
            <span style={{ color: 'var(--text-secondary)', marginInlineStart: 8 }}>
              {c.symbol}
            </span>
          </button>
        ))}
      </div>
    </StepShell>
  );
}
