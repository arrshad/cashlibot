import { useState } from 'react';
import { t } from '@/i18n';
import { StepShell } from './StepShell';
import type { Lang, TimezoneOption } from '@/types';

type Props = {
  lang: Lang;
  step: number;
  total: number;
  value: string | undefined;
  options: TimezoneOption[];
  onPick: (tz: string) => void;
  onBack: () => void;
};

function isValidTimezone(tz: string): boolean {
  try {
    new Intl.DateTimeFormat(undefined, { timeZone: tz });
    return true;
  } catch {
    return false;
  }
}

export function TimezoneStep({
  lang,
  step,
  total,
  value,
  options,
  onPick,
  onBack,
}: Props) {
  const presetValues = new Set(options.map((o) => o.name));
  const startsCustom = !!value && !presetValues.has(value);
  const [custom, setCustom] = useState(startsCustom);
  const [text, setText] = useState(startsCustom ? value! : '');
  const [error, setError] = useState<string | null>(null);

  const submitCustom = () => {
    const trimmed = text.trim();
    if (!isValidTimezone(trimmed)) {
      setError(t(lang, 'onboarding.timezone.invalid'));
      return;
    }
    setError(null);
    onPick(trimmed);
  };

  return (
    <StepShell
      lang={lang}
      step={step}
      total={total}
      title={t(lang, 'onboarding.timezone.title')}
      subtitle={t(lang, 'onboarding.timezone.subtitle')}
      canBack
      onBack={onBack}
      primaryLabel={custom ? t(lang, 'common.continue') : undefined}
      onPrimary={custom ? submitCustom : undefined}
      primaryDisabled={custom && !text.trim()}
    >
      {custom ? (
        <div className="field">
          <input
            className="input"
            placeholder={t(lang, 'onboarding.timezone.custom_placeholder')}
            value={text}
            onChange={(e) => {
              setText(e.target.value);
              setError(null);
            }}
            autoFocus
          />
          {error && <span className="error-text">{error}</span>}
          <button
            className="btn btn-ghost"
            style={{ marginTop: 6 }}
            onClick={() => {
              setCustom(false);
              setText('');
              setError(null);
            }}
          >
            {t(lang, 'common.back')}
          </button>
        </div>
      ) : (
        <div className="choice-grid">
          {options.map((opt) => (
            <button
              key={opt.name}
              className={`btn ${value === opt.name ? 'btn-selected' : ''}`}
              onClick={() => onPick(opt.name)}
            >
              {opt.label}
            </button>
          ))}
          <button
            className="btn"
            style={{ gridColumn: '1 / -1' }}
            onClick={() => setCustom(true)}
          >
            {t(lang, 'onboarding.timezone.other')}
          </button>
        </div>
      )}
    </StepShell>
  );
}
