import { useState } from 'react';
import { completeOnboarding } from '@/api/client';
import { applyHtmlLang } from '@/i18n';
import { useAppStore } from '@/store/app';
import { AccountStep } from './AccountStep';
import { CalendarStep } from './CalendarStep';
import { CurrencyStep } from './CurrencyStep';
import { DoneScreen } from './DoneScreen';
import { LanguageStep } from './LanguageStep';
import { TimezoneStep } from './TimezoneStep';
import type { AccountType, CalendarSystem, Lang } from '@/types';

const TOTAL = 5;

type Draft = {
  language_code?: Lang;
  calendar_system?: CalendarSystem;
  timezone?: string;
  default_currency?: string;
};

type DonePayload = { credits: number };

export function Onboarding() {
  const me = useAppStore((s) => s.me!);
  const config = useAppStore((s) => s.config!);
  const setMe = useAppStore((s) => s.setMe);

  const [step, setStep] = useState(0);
  const [draft, setDraft] = useState<Draft>({});
  const [submitting, setSubmitting] = useState(false);
  const [submitError, setSubmitError] = useState<string | null>(null);
  const [done, setDone] = useState<DonePayload | null>(null);

  // Effective UI language: whatever the user has chosen so far, else their
  // Telegram-reported language from `me`.
  const uiLang: Lang = draft.language_code ?? me.language_code;

  const advance = () => setStep((s) => Math.min(s + 1, TOTAL - 1));
  const goBack = () => setStep((s) => Math.max(s - 1, 0));

  const submitAccount = async (account: {
    name: string;
    type: AccountType;
    currency: string;
  }) => {
    if (
      !draft.language_code ||
      !draft.calendar_system ||
      !draft.timezone ||
      !draft.default_currency
    ) {
      return;
    }
    setSubmitting(true);
    setSubmitError(null);
    try {
      const result = await completeOnboarding({
        language_code: draft.language_code,
        calendar_system: draft.calendar_system,
        timezone: draft.timezone,
        default_currency: draft.default_currency,
        first_account: account,
      });
      setMe({
        ...me,
        language_code: draft.language_code,
        calendar_system: draft.calendar_system,
        timezone: draft.timezone,
        default_currency: draft.default_currency,
        credit_balance: result.credit_balance,
        onboarding_completed: true,
      });
      setDone({ credits: result.signup_credits_granted });
    } catch (err) {
      const msg = err instanceof Error ? err.message : 'failed';
      setSubmitError(msg);
    } finally {
      setSubmitting(false);
    }
  };

  if (done) return <DoneScreen lang={uiLang} credits={done.credits} />;

  if (step === 0) {
    return (
      <LanguageStep
        lang={uiLang}
        step={step}
        total={TOTAL}
        value={draft.language_code}
        onPick={(l) => {
          applyHtmlLang(l);
          setDraft({ ...draft, language_code: l });
          advance();
        }}
      />
    );
  }
  if (step === 1) {
    return (
      <CalendarStep
        lang={uiLang}
        step={step}
        total={TOTAL}
        value={draft.calendar_system}
        onPick={(c) => {
          setDraft({ ...draft, calendar_system: c });
          advance();
        }}
        onBack={goBack}
      />
    );
  }
  if (step === 2) {
    return (
      <TimezoneStep
        lang={uiLang}
        step={step}
        total={TOTAL}
        value={draft.timezone}
        options={config.timezones}
        onPick={(tz) => {
          setDraft({ ...draft, timezone: tz });
          advance();
        }}
        onBack={goBack}
      />
    );
  }
  if (step === 3) {
    return (
      <CurrencyStep
        lang={uiLang}
        step={step}
        total={TOTAL}
        value={draft.default_currency}
        options={config.currencies}
        onPick={(code) => {
          setDraft({ ...draft, default_currency: code });
          advance();
        }}
        onBack={goBack}
      />
    );
  }
  return (
    <>
      <AccountStep
        lang={uiLang}
        step={step}
        total={TOTAL}
        initialCurrency={draft.default_currency!}
        currencies={config.currencies}
        accountTypes={config.account_types}
        onSubmit={submitAccount}
        onBack={goBack}
        submitting={submitting}
      />
      {submitError && (
        <div className="app-shell" style={{ paddingTop: 0 }}>
          <div className="app-frame">
            <div className="glass-card" style={{ padding: 16 }}>
              <p className="error-text">{submitError}</p>
            </div>
          </div>
        </div>
      )}
    </>
  );
}
