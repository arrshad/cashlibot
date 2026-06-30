import type { ReactNode } from 'react';
import { t } from '@/i18n';
import type { Lang } from '@/types';

type Props = {
  lang: Lang;
  step: number;
  total: number;
  title: string;
  subtitle?: string;
  children: ReactNode;
  primaryLabel?: string;
  onPrimary?: () => void;
  primaryDisabled?: boolean;
  canBack?: boolean;
  onBack?: () => void;
};

export function StepShell({
  lang,
  step,
  total,
  title,
  subtitle,
  children,
  primaryLabel,
  onPrimary,
  primaryDisabled,
  canBack,
  onBack,
}: Props) {
  return (
    <div className="app-shell">
      <div className="app-frame">
        <div className="glass-card" style={{ padding: 22 }}>
          <div className="step">
            <div className="step-header">
              <span>
                {step + 1} / {total}
              </span>
            </div>
            <h2 className="step-title">{title}</h2>
            {subtitle && <p className="step-subtitle">{subtitle}</p>}
            <div className="step-body">{children}</div>
            {(onPrimary || canBack) && (
              <div className="step-footer">
                {canBack && (
                  <button className="btn btn-ghost" onClick={onBack}>
                    {t(lang, 'common.back')}
                  </button>
                )}
                {onPrimary && primaryLabel && (
                  <button
                    className="btn btn-primary"
                    onClick={onPrimary}
                    disabled={primaryDisabled}
                  >
                    {primaryLabel}
                  </button>
                )}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
