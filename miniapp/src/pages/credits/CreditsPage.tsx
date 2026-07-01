import { useEffect } from 'react';
import { Icon } from '@/components/Icon';
import { t } from '@/i18n';
import { useAppStore } from '@/store/app';
import { useCreditsStore } from '@/store/credits';
import { useNavStore } from '@/store/nav';
import { formatDate } from '@/util/format-date';
import type { CreditHistoryEntry } from '@/types';

export function CreditsPage() {
  const me = useAppStore((s) => s.me!);
  const lang = me.language_code;
  const { status, loading, error, load } = useCreditsStore();
  const go = useNavStore((s) => s.go);

  useEffect(() => {
    load();
  }, [load]);

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
          <h2 className="step-title">{t(lang, 'credits.title')}</h2>
        </div>

        {error && (
          <div className="glass-card" style={{ padding: 16 }}>
            <span className="error-text">{error}</span>
          </div>
        )}

        {loading && !status && (
          <div className="glass-card" style={{ padding: 16 }}>
            {t(lang, 'common.loading')}
          </div>
        )}

        {status && (
          <>
            <div className="glass-card credits-balance">
              <span className="field-label">{t(lang, 'credits.balance_label')}</span>
              <span className="credits-balance-value">
                {status.balance.toLocaleString()}
              </span>
              <span className="hint-text">{t(lang, 'credits.balance_hint')}</span>
            </div>

            <section className="section">
              <div className="section-header">
                <h3 className="section-title">{t(lang, 'credits.buy_title')}</h3>
              </div>
              <div className="credits-packages">
                {status.packages.map((p) => (
                  <button
                    key={p.stars}
                    className="glass-card credits-package"
                    onClick={() =>
                      alert(t(lang, 'credits.purchase_via_bot'))
                    }
                  >
                    <span className="credits-package-label">{p.label}</span>
                    <span className="credits-package-credits">
                      {t(lang, 'credits.credits_amount', {
                        amount: p.credits.toLocaleString(),
                      })}
                    </span>
                    <span className="credits-package-price">
                      {t(lang, 'credits.stars_price', { stars: p.stars })}
                    </span>
                  </button>
                ))}
              </div>
              <p className="hint-text center" style={{ marginTop: 8 }}>
                {t(lang, 'credits.purchase_via_bot')}
              </p>
            </section>

            <section className="section">
              <div className="section-header">
                <h3 className="section-title">{t(lang, 'credits.history_title')}</h3>
              </div>
              {status.history.length === 0 ? (
                <div className="glass-card" style={{ padding: 16 }}>
                  <span className="hint-text">{t(lang, 'credits.history_empty')}</span>
                </div>
              ) : (
                <div className="credit-history">
                  {status.history.map((entry) => (
                    <HistoryRow key={entry.id} entry={entry} lang={lang} />
                  ))}
                </div>
              )}
            </section>
          </>
        )}
      </div>
    </div>
  );
}

function HistoryRow({
  entry,
  lang,
}: {
  entry: CreditHistoryEntry;
  lang: 'en' | 'fa';
}) {
  const me = useAppStore((s) => s.me!);
  const positive = entry.change_amount > 0;
  return (
    <div className="glass-card history-row">
      <div className="history-row-body">
        <span className="history-row-reason">
          {t(lang, `credits.reason.${entry.reason}`)}
        </span>
        <span className="history-row-date">
          {formatDate(entry.created_at, lang, me.calendar_system, me.timezone, 'short')}
        </span>
      </div>
      <span
        className="history-row-amount"
        style={{ color: positive ? 'var(--accent-success)' : 'var(--accent-danger)' }}
      >
        {positive ? '+' : ''}
        {entry.change_amount}
      </span>
    </div>
  );
}
