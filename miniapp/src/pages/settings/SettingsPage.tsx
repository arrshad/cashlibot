import { useState } from 'react';
import { patchMe } from '@/api/client';
import { Icon } from '@/components/Icon';
import { applyHtmlLang, t } from '@/i18n';
import { useAppStore } from '@/store/app';
import { useNavStore } from '@/store/nav';
import type {
  CalendarSystem,
  Lang,
  UserPatchPayload,
} from '@/types';

const POPULAR_TIMEZONES: string[] = [
  'Asia/Tehran',
  'Asia/Dubai',
  'Europe/Istanbul',
  'Europe/London',
  'Europe/Paris',
  'America/New_York',
  'America/Los_Angeles',
  'Asia/Tokyo',
  'UTC',
];

const CALENDARS: CalendarSystem[] = ['gregorian', 'jalali', 'hijri'];

function isValidTz(tz: string): boolean {
  try {
    new Intl.DateTimeFormat(undefined, { timeZone: tz });
    return true;
  } catch {
    return false;
  }
}

export function SettingsPage() {
  const me = useAppStore((s) => s.me!);
  const config = useAppStore((s) => s.config!);
  const setMe = useAppStore((s) => s.setMe);
  const go = useNavStore((s) => s.go);
  const lang = me.language_code;

  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Free-text timezone entry when the user picks "Other".
  const startsCustom = !POPULAR_TIMEZONES.includes(me.timezone);
  const [tzCustom, setTzCustom] = useState(startsCustom);
  const [tzText, setTzText] = useState(startsCustom ? me.timezone : '');
  const [tzError, setTzError] = useState<string | null>(null);

  const apply = async (patch: UserPatchPayload) => {
    setSaving(true);
    setError(null);
    try {
      const updated = await patchMe(patch);
      setMe(updated);
      if (patch.language_code) applyHtmlLang(patch.language_code);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'failed to save');
    } finally {
      setSaving(false);
    }
  };

  const submitTz = () => {
    const value = tzText.trim();
    if (!isValidTz(value)) {
      setTzError(t(lang, 'onboarding.timezone.invalid'));
      return;
    }
    setTzError(null);
    apply({ timezone: value });
    setTzCustom(false);
  };

  return (
    <div className="app-shell">
      <div className="app-frame">
        <div className="page-header">
          <button
            className="icon-btn"
            onClick={() => go({ name: 'dashboard' })}
            aria-label={t(lang, 'common.back')}
          >
            <Icon name="fa-arrow-left" />
          </button>
          <h2 className="step-title">{t(lang, 'settings.title')}</h2>
          {saving && (
            <span className="hint-text" style={{ marginInlineStart: 'auto' }}>
              {t(lang, 'settings.saving')}
            </span>
          )}
        </div>

        {error && (
          <div className="glass-card" style={{ padding: 16 }}>
            <span className="error-text">{error}</span>
          </div>
        )}

        {/* Language */}
        <section className="glass-card settings-card">
          <span className="field-label">{t(lang, 'settings.language')}</span>
          <div className="choice-grid">
            {(['en', 'fa'] as Lang[]).map((code) => (
              <button
                key={code}
                className={`btn ${me.language_code === code ? 'btn-selected' : ''}`}
                onClick={() => apply({ language_code: code })}
              >
                {code === 'en' ? 'English' : 'فارسی'}
              </button>
            ))}
          </div>
        </section>

        {/* Calendar */}
        <section className="glass-card settings-card">
          <span className="field-label">{t(lang, 'settings.calendar')}</span>
          <div className="choice-grid">
            {CALENDARS.map((c) => (
              <button
                key={c}
                className={`btn ${me.calendar_system === c ? 'btn-selected' : ''}`}
                onClick={() => apply({ calendar_system: c })}
              >
                {t(lang, `onboarding.calendar.${c}`)}
              </button>
            ))}
          </div>
        </section>

        {/* Timezone */}
        <section className="glass-card settings-card">
          <span className="field-label">{t(lang, 'settings.timezone')}</span>
          {tzCustom ? (
            <div className="field">
              <input
                className="input"
                placeholder={t(lang, 'onboarding.timezone.custom_placeholder')}
                value={tzText}
                onChange={(e) => {
                  setTzText(e.target.value);
                  setTzError(null);
                }}
                autoFocus
              />
              {tzError && <span className="error-text">{tzError}</span>}
              <div style={{ display: 'flex', gap: 8, marginTop: 6 }}>
                <button
                  className="btn btn-ghost"
                  onClick={() => {
                    setTzCustom(false);
                    setTzError(null);
                  }}
                >
                  {t(lang, 'common.cancel')}
                </button>
                <button
                  className="btn btn-primary"
                  disabled={!tzText.trim() || saving}
                  onClick={submitTz}
                >
                  {t(lang, 'common.done')}
                </button>
              </div>
            </div>
          ) : (
            <div className="choice-grid">
              {POPULAR_TIMEZONES.map((tz) => (
                <button
                  key={tz}
                  className={`btn ${me.timezone === tz ? 'btn-selected' : ''}`}
                  onClick={() => apply({ timezone: tz })}
                >
                  {tz.split('/').pop()!.replace('_', ' ')}
                </button>
              ))}
              <button
                className={`btn ${startsCustom ? 'btn-selected' : ''}`}
                style={{ gridColumn: '1 / -1' }}
                onClick={() => setTzCustom(true)}
              >
                {t(lang, 'common.other')}
                {startsCustom && `: ${me.timezone}`}
              </button>
            </div>
          )}
        </section>

        {/* Default currency */}
        <section className="glass-card settings-card">
          <span className="field-label">{t(lang, 'settings.default_currency')}</span>
          <div className="choice-grid">
            {config.currencies.map((c) => (
              <button
                key={c.code}
                className={`btn ${me.default_currency === c.code ? 'btn-selected' : ''}`}
                onClick={() => apply({ default_currency: c.code })}
              >
                <span style={{ fontWeight: 600 }}>{c.code}</span>
                <span
                  style={{ color: 'var(--text-secondary)', marginInlineStart: 8 }}
                >
                  {c.symbol}
                </span>
              </button>
            ))}
          </div>
        </section>
      </div>
    </div>
  );
}
