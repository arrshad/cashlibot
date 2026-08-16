import { useState } from 'react';
import { downloadExport, patchMe } from '@/api/client';
import { Icon } from '@/components/Icon';
import { MenuRow } from '@/components/MenuRow';
import { PickerSheet, type PickerOption } from '@/components/PickerSheet';
import { Sheet } from '@/components/Sheet';
import { applyHtmlLang, t } from '@/i18n';
import { useAppStore } from '@/store/app';
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

const DIGEST_DAYS: { dow: number; key: string }[] = [
  { dow: 0, key: 'settings.digest.day.mon' },
  { dow: 1, key: 'settings.digest.day.tue' },
  { dow: 2, key: 'settings.digest.day.wed' },
  { dow: 3, key: 'settings.digest.day.thu' },
  { dow: 4, key: 'settings.digest.day.fri' },
  { dow: 5, key: 'settings.digest.day.sat' },
  { dow: 6, key: 'settings.digest.day.sun' },
];

type Picker =
  | null
  | { kind: 'language' }
  | { kind: 'calendar' }
  | { kind: 'timezone' }
  | { kind: 'currency' }
  | { kind: 'digest' }
  | { kind: 'export' }
  | { kind: 'profile' };

export function SettingsPage() {
  const me = useAppStore((s) => s.me!);
  const config = useAppStore((s) => s.config!);
  const setMe = useAppStore((s) => s.setMe);
  const lang = me.language_code;

  const [picker, setPicker] = useState<Picker>(null);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

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

  const currencyLabel = (code: string | null) => {
    if (!code) return '—';
    const c = config.currencies.find((x) => x.code === code);
    return c ? `${c.code} · ${c.symbol}` : code;
  };

  const tzShort = (tz: string) =>
    tz.split('/').pop()?.replace('_', ' ') ?? tz;

  return (
    <div className="app-shell has-tabbar">
      <div className="app-frame">
        <h2 className="step-title" style={{ margin: '4px 4px 4px' }}>
          {t(lang, 'settings.title')}
        </h2>

        {error && (
          <div className="glass-card" style={{ padding: 16 }}>
            <span className="error-text">{error}</span>
          </div>
        )}

        {/* Profile */}
        <div className="profile-card">
          <div className="profile-avatar">
            {me.display_name.trim().charAt(0).toUpperCase() || '?'}
          </div>
          <div className="profile-body">
            <span className="profile-name">{me.display_name}</span>
            <span className="profile-sub">
              {me.username ? `@${me.username}` : `id ${me.telegram_id}`}
            </span>
          </div>
          <button
            className="icon-btn"
            onClick={() => setPicker({ kind: 'profile' })}
            aria-label={t(lang, 'settings.profile.edit')}
          >
            <Icon name="fa-pencil" />
          </button>
        </div>

        {/* General */}
        <div className="list-section">
          <MenuRow
            icon="fa-language"
            tint="purple"
            title={t(lang, 'settings.language')}
            value={lang === 'en' ? 'English' : 'فارسی'}
            onClick={() => setPicker({ kind: 'language' })}
          />
          <MenuRow
            icon="fa-calendar"
            tint="orange"
            title={t(lang, 'settings.calendar')}
            value={t(lang, `onboarding.calendar.${me.calendar_system}`)}
            onClick={() => setPicker({ kind: 'calendar' })}
          />
          <MenuRow
            icon="fa-clock"
            tint="blue"
            title={t(lang, 'settings.timezone')}
            value={tzShort(me.timezone)}
            onClick={() => setPicker({ kind: 'timezone' })}
          />
          <MenuRow
            icon="fa-dollar-sign"
            tint="green"
            title={t(lang, 'settings.default_currency')}
            value={currencyLabel(me.default_currency)}
            onClick={() => setPicker({ kind: 'currency' })}
          />
        </div>

        {/* Notifications + Data */}
        <div className="list-section">
          <MenuRow
            icon="fa-bell"
            tint="red"
            title={t(lang, 'settings.digest.title')}
            value={
              me.weekly_digest_enabled
                ? t(lang, 'common.on')
                : t(lang, 'common.off')
            }
            onClick={() => setPicker({ kind: 'digest' })}
          />
          <MenuRow
            icon="fa-arrow-down"
            tint="teal"
            title={t(lang, 'settings.export.title')}
            onClick={() => setPicker({ kind: 'export' })}
          />
        </div>

        {saving && (
          <span className="hint-text" style={{ textAlign: 'center' }}>
            {t(lang, 'settings.saving')}
          </span>
        )}
      </div>

      {picker?.kind === 'language' && (
        <PickerSheet
          title={t(lang, 'settings.language')}
          value={lang}
          onChange={(v) => apply({ language_code: v as Lang })}
          onClose={() => setPicker(null)}
          options={[
            { value: 'en', label: 'English' },
            { value: 'fa', label: 'فارسی' },
          ]}
        />
      )}
      {picker?.kind === 'calendar' && (
        <PickerSheet
          title={t(lang, 'settings.calendar')}
          value={me.calendar_system}
          onChange={(v) =>
            apply({ calendar_system: v as CalendarSystem })
          }
          onClose={() => setPicker(null)}
          options={CALENDARS.map((c): PickerOption<string> => ({
            value: c,
            label: t(lang, `onboarding.calendar.${c}`),
          }))}
        />
      )}
      {picker?.kind === 'timezone' && (
        <TimezonePicker
          value={me.timezone}
          onChange={(tz) => apply({ timezone: tz })}
          onClose={() => setPicker(null)}
          lang={lang}
        />
      )}
      {picker?.kind === 'currency' && (
        <PickerSheet
          title={t(lang, 'settings.default_currency')}
          value={me.default_currency ?? ''}
          onChange={(v) => apply({ default_currency: v as string })}
          onClose={() => setPicker(null)}
          options={config.currencies.map(
            (c): PickerOption<string> => ({
              value: c.code,
              label: `${c.code} · ${c.symbol}`,
              hint: c.name,
            }),
          )}
        />
      )}
      {picker?.kind === 'digest' && (
        <DigestPicker
          lang={lang}
          enabled={me.weekly_digest_enabled}
          hour={me.weekly_digest_hour}
          dow={me.weekly_digest_dow}
          onChange={apply}
          onClose={() => setPicker(null)}
        />
      )}
      {picker?.kind === 'export' && (
        <ExportPicker lang={lang} onClose={() => setPicker(null)} />
      )}
      {picker?.kind === 'profile' && (
        <ProfilePicker
          initial={me.display_name}
          lang={lang}
          onSubmit={async (name) => {
            await apply({ display_name: name } as UserPatchPayload);
          }}
          onClose={() => setPicker(null)}
        />
      )}
    </div>
  );
}

function TimezonePicker({
  value,
  onChange,
  onClose,
  lang,
}: {
  value: string;
  onChange: (v: string) => void;
  onClose: () => void;
  lang: Lang;
}) {
  const [custom, setCustom] = useState('');
  return (
    <Sheet
      title={t(lang, 'settings.timezone')}
      onClose={onClose}
      footer={
        custom.trim().length > 0 && (
          <button
            className="btn btn-primary"
            onClick={() => {
              onChange(custom.trim());
              onClose();
            }}
          >
            {t(lang, 'common.done')}
          </button>
        )
      }
    >
      <input
        className="input"
        placeholder={t(lang, 'onboarding.timezone.custom_placeholder')}
        value={custom}
        onChange={(e) => setCustom(e.target.value)}
      />
      <div className="picker-list">
        {POPULAR_TIMEZONES.map((tz) => {
          const active = tz === value;
          return (
            <button
              key={tz}
              className={`picker-row${active ? ' active' : ''}`}
              onClick={() => {
                onChange(tz);
                onClose();
              }}
            >
              <span className="picker-row-label">{tz}</span>
              {active && (
                <span className="picker-row-check">
                  <Icon name="fa-check" />
                </span>
              )}
            </button>
          );
        })}
      </div>
    </Sheet>
  );
}

function DigestPicker({
  lang,
  enabled,
  hour,
  dow,
  onChange,
  onClose,
}: {
  lang: Lang;
  enabled: boolean;
  hour: number;
  dow: number;
  onChange: (p: UserPatchPayload) => Promise<void>;
  onClose: () => void;
}) {
  const [h, setH] = useState(String(hour));
  return (
    <Sheet
      title={t(lang, 'settings.digest.title')}
      onClose={onClose}
      footer={
        <button
          className="btn btn-primary"
          onClick={async () => {
            const parsed = Math.max(0, Math.min(23, Number(h) || 0));
            await onChange({ weekly_digest_hour: parsed });
            onClose();
          }}
        >
          {t(lang, 'common.done')}
        </button>
      }
    >
      <p className="hint-text" style={{ marginTop: -4 }}>
        {t(lang, 'settings.digest.subtitle')}
      </p>

      <div className="picker-list">
        <button
          className={`picker-row${enabled ? ' active' : ''}`}
          onClick={() => onChange({ weekly_digest_enabled: true })}
        >
          <span className="picker-row-label">{t(lang, 'common.on')}</span>
          {enabled && (
            <span className="picker-row-check">
              <Icon name="fa-check" />
            </span>
          )}
        </button>
        <button
          className={`picker-row${!enabled ? ' active' : ''}`}
          onClick={() => onChange({ weekly_digest_enabled: false })}
        >
          <span className="picker-row-label">{t(lang, 'common.off')}</span>
          {!enabled && (
            <span className="picker-row-check">
              <Icon name="fa-check" />
            </span>
          )}
        </button>
      </div>

      {enabled && (
        <>
          <div className="field">
            <span className="field-label">
              {t(lang, 'settings.digest.day')}
            </span>
            <div className="picker-list">
              {DIGEST_DAYS.map(({ dow: v, key }) => (
                <button
                  key={v}
                  className={`picker-row${dow === v ? ' active' : ''}`}
                  onClick={() => onChange({ weekly_digest_dow: v })}
                >
                  <span className="picker-row-label">{t(lang, key)}</span>
                  {dow === v && (
                    <span className="picker-row-check">
                      <Icon name="fa-check" />
                    </span>
                  )}
                </button>
              ))}
            </div>
          </div>

          <div className="field">
            <span className="field-label">
              {t(lang, 'settings.digest.hour')}
            </span>
            <input
              className="input"
              type="text"
              inputMode="numeric"
              maxLength={2}
              value={h}
              onChange={(e) =>
                setH(e.target.value.replace(/[^0-9]/g, '').slice(0, 2))
              }
              placeholder="09"
            />
          </div>
        </>
      )}
    </Sheet>
  );
}

function ExportPicker({
  lang,
  onClose,
}: {
  lang: Lang;
  onClose: () => void;
}) {
  const [exporting, setExporting] = useState<'json' | 'csv' | null>(null);
  const [err, setErr] = useState<string | null>(null);

  const download = async (kind: 'json' | 'csv') => {
    setExporting(kind);
    setErr(null);
    try {
      await downloadExport(
        kind === 'json'
          ? '/api/export/data.json'
          : '/api/export/transactions.csv',
      );
      onClose();
    } catch {
      setErr(t(lang, 'settings.export.failed'));
    } finally {
      setExporting(null);
    }
  };

  return (
    <Sheet title={t(lang, 'settings.export.title')} onClose={onClose}>
      <p className="hint-text" style={{ marginTop: -4 }}>
        {t(lang, 'settings.export.subtitle')}
      </p>
      {err && <span className="error-text">{err}</span>}
      <div className="picker-list">
        <button
          className="picker-row"
          disabled={exporting !== null}
          onClick={() => download('json')}
        >
          <span className="picker-row-label">
            {t(lang, 'settings.export.download_json')}
            <span className="picker-row-hint">JSON</span>
          </span>
          {exporting === 'json' && (
            <span className="picker-row-check">…</span>
          )}
        </button>
        <button
          className="picker-row"
          disabled={exporting !== null}
          onClick={() => download('csv')}
        >
          <span className="picker-row-label">
            {t(lang, 'settings.export.download_csv')}
            <span className="picker-row-hint">CSV</span>
          </span>
          {exporting === 'csv' && (
            <span className="picker-row-check">…</span>
          )}
        </button>
      </div>
    </Sheet>
  );
}

function ProfilePicker({
  initial,
  lang,
  onSubmit,
  onClose,
}: {
  initial: string;
  lang: Lang;
  onSubmit: (name: string) => Promise<void>;
  onClose: () => void;
}) {
  const [name, setName] = useState(initial);
  const [busy, setBusy] = useState(false);
  return (
    <Sheet
      title={t(lang, 'settings.profile.edit')}
      onClose={onClose}
      footer={
        <button
          className="btn btn-primary"
          disabled={busy || name.trim().length === 0}
          onClick={async () => {
            setBusy(true);
            await onSubmit(name.trim());
            setBusy(false);
            onClose();
          }}
        >
          {t(lang, 'common.done')}
        </button>
      }
    >
      <div className="field">
        <span className="field-label">
          {t(lang, 'settings.profile.name_label')}
        </span>
        <input
          className="input"
          value={name}
          maxLength={64}
          onChange={(e) => setName(e.target.value)}
          autoFocus
        />
      </div>
    </Sheet>
  );
}
