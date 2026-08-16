import { useState } from 'react';
import { ConfirmDialog } from '@/components/ConfirmDialog';
import { Icon } from '@/components/Icon';
import { Sheet } from '@/components/Sheet';
import { t } from '@/i18n';
import { useAppStore } from '@/store/app';
import { useDashboardStore } from '@/store/dashboard';
import type { Account, AccountType, Lang } from '@/types';

type Props = {
  account: Account;
  lang: Lang;
  onClose: () => void;
};

// Palette matches the tints defined in globals.css.
const COLOR_SWATCHES = [
  '#30d158', // green
  '#0a84ff', // blue
  '#bf5af2', // purple
  '#ff9f0a', // orange
  '#ff375f', // pink
  '#64d2ff', // teal
  '#ffd60a', // yellow
  '#8e8e93', // graphite
];

// A curated set of Font Awesome glyphs that make sense for accounts.
const ICON_CHOICES = [
  'fa-wallet',
  'fa-credit-card',
  'fa-building-columns',
  'fa-piggy-bank',
  'fa-mobile-screen',
  'fa-coins',
  'fa-money-bill-wave',
  'fa-chart-line',
  'fa-vault',
  'fa-money-check',
];

const ACCOUNT_TYPES: AccountType[] = [
  'cash',
  'card',
  'bank',
  'e_wallet',
  'credit',
  'investment',
  'savings',
];

export function AccountEditSheet({ account, lang, onClose }: Props) {
  const config = useAppStore((s) => s.config!);
  const update = useDashboardStore((s) => s.updateAccount);
  const archive = useDashboardStore((s) => s.archiveAccount);

  const [name, setName] = useState(account.name);
  const [icon, setIcon] = useState(account.icon || 'fa-wallet');
  const [color, setColor] = useState<string | null>(account.color ?? null);
  const [type, setType] = useState<AccountType>(account.type);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const dirty =
    name.trim() !== account.name ||
    icon !== (account.icon || 'fa-wallet') ||
    color !== (account.color ?? null) ||
    type !== account.type;

  const save = async () => {
    if (!dirty) {
      onClose();
      return;
    }
    setSaving(true);
    setError(null);
    try {
      await update(account.id, {
        name: name.trim(),
        icon,
        color,
        type,
      });
      onClose();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'failed to save');
    } finally {
      setSaving(false);
    }
  };

  const [confirming, setConfirming] = useState(false);
  const runDelete = async () => {
    setSaving(true);
    try {
      await archive(account.id);
      onClose();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'failed to delete');
      setSaving(false);
    }
  };

  return (
    <Sheet
      title={t(lang, 'account.edit.title')}
      onClose={onClose}
      footer={
        <button
          className="btn btn-primary"
          onClick={save}
          disabled={saving || name.trim().length === 0}
        >
          {saving ? t(lang, 'settings.saving') : t(lang, 'common.done')}
        </button>
      }
    >
      {error && <span className="error-text">{error}</span>}

      <div className="field">
        <label className="field-label">{t(lang, 'account.edit.name')}</label>
        <input
          className="input"
          value={name}
          onChange={(e) => setName(e.target.value)}
          maxLength={40}
        />
      </div>

      <div className="field">
        <span className="field-label">{t(lang, 'account.edit.icon')}</span>
        <div className="choice-grid" style={{ gridTemplateColumns: 'repeat(5, minmax(0, 1fr))' }}>
          {ICON_CHOICES.map((glyph) => (
            <button
              key={glyph}
              className={`btn${icon === glyph ? ' btn-selected' : ''}`}
              onClick={() => setIcon(glyph)}
              aria-label={glyph}
              style={{ padding: '10px 0', fontSize: 16 }}
            >
              <Icon name={glyph} />
            </button>
          ))}
        </div>
      </div>

      <div className="field">
        <span className="field-label">{t(lang, 'account.edit.color')}</span>
        <div className="swatch-row">
          <button
            className={`swatch${color === null ? ' selected' : ''}`}
            style={{ background: 'transparent', border: '2px dashed rgba(255,255,255,0.3)' }}
            onClick={() => setColor(null)}
            aria-label={t(lang, 'account.edit.color_none')}
          />
          {COLOR_SWATCHES.map((hex) => (
            <button
              key={hex}
              className={`swatch${color === hex ? ' selected' : ''}`}
              style={{ background: hex }}
              onClick={() => setColor(hex)}
              aria-label={hex}
            />
          ))}
        </div>
      </div>

      <div className="field">
        <span className="field-label">{t(lang, 'account.edit.type')}</span>
        <div className="choice-grid" style={{ gridTemplateColumns: 'repeat(3, minmax(0, 1fr))' }}>
          {ACCOUNT_TYPES.map((tp) => {
            const opt = config.account_types.find((a) => a.value === tp);
            return (
              <button
                key={tp}
                className={`btn${type === tp ? ' btn-selected' : ''}`}
                onClick={() => setType(tp)}
                style={{ padding: '10px 8px', fontSize: 12 }}
              >
                <Icon name={opt?.icon ?? 'fa-wallet'} />
                <span>{t(lang, `onboarding.account.type.${tp}`)}</span>
              </button>
            );
          })}
        </div>
      </div>

      <button
        className="btn"
        onClick={() => setConfirming(true)}
        disabled={saving}
        style={{ color: 'var(--accent-danger)', justifyContent: 'center' }}
      >
        <Icon name="fa-trash" /> {t(lang, 'account.edit.delete')}
      </button>
      {confirming && (
        <ConfirmDialog
          title={t(lang, 'account.edit.delete')}
          message={t(lang, 'account.edit.delete_confirm')}
          confirmLabel={t(lang, 'confirm.delete')}
          cancelLabel={t(lang, 'confirm.cancel')}
          destructive
          onCancel={() => setConfirming(false)}
          onConfirm={() => {
            setConfirming(false);
            void runDelete();
          }}
        />
      )}
    </Sheet>
  );
}
