import { t } from '@/i18n';
import { StepShell } from './StepShell';
import type { Lang } from '@/types';

type Props = {
  lang: Lang;
  step: number;
  total: number;
  value: Lang | undefined;
  onPick: (lang: Lang) => void;
};

export function LanguageStep({ lang, step, total, value, onPick }: Props) {
  // The title shows in BOTH languages so the user can recognize their own
  // before they've made a choice.
  const title =
    lang === 'fa'
      ? `${t('fa', 'onboarding.language.title')} / ${t('en', 'onboarding.language.title')}`
      : `${t('en', 'onboarding.language.title')} / ${t('fa', 'onboarding.language.title')}`;

  return (
    <StepShell
      lang={lang}
      step={step}
      total={total}
      title={title}
      subtitle={t(lang, 'onboarding.language.subtitle')}
    >
      <div className="choice-grid">
        <button
          className={`btn ${value === 'en' ? 'btn-selected' : ''}`}
          onClick={() => onPick('en')}
        >
          English
        </button>
        <button
          className={`btn ${value === 'fa' ? 'btn-selected' : ''}`}
          onClick={() => onPick('fa')}
        >
          فارسی
        </button>
      </div>
    </StepShell>
  );
}
