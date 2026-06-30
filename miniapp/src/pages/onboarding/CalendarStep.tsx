import { t } from '@/i18n';
import { StepShell } from './StepShell';
import type { CalendarSystem, Lang } from '@/types';

type Props = {
  lang: Lang;
  step: number;
  total: number;
  value: CalendarSystem | undefined;
  onPick: (cal: CalendarSystem) => void;
  onBack: () => void;
};

const ORDER: CalendarSystem[] = ['gregorian', 'jalali', 'hijri'];

export function CalendarStep({ lang, step, total, value, onPick, onBack }: Props) {
  return (
    <StepShell
      lang={lang}
      step={step}
      total={total}
      title={t(lang, 'onboarding.calendar.title')}
      subtitle={t(lang, 'onboarding.calendar.subtitle')}
      canBack
      onBack={onBack}
    >
      <div className="choice-list">
        {ORDER.map((cal) => (
          <button
            key={cal}
            className={`btn ${value === cal ? 'btn-selected' : ''}`}
            onClick={() => onPick(cal)}
          >
            {t(lang, `onboarding.calendar.${cal}`)}
          </button>
        ))}
      </div>
    </StepShell>
  );
}
