import { useEffect, useState } from 'react';
import { createPurchaseInvoice } from '@/api/client';
import { Icon } from '@/components/Icon';
import { t } from '@/i18n';
import { useAppStore } from '@/store/app';
import { useCreditsStore } from '@/store/credits';
import { useNavStore } from '@/store/nav';
import { openTelegramInvoice } from '@/telegram';
import { formatDate } from '@/util/format-date';
import type { CreditHistoryEntry } from '@/types';

export function CreditsPage() {
  const me = useAppStore((s) => s.me!);
  const refreshMe = useAppStore((s) => s.refreshMe);
  const lang = me.language_code;
  const { status, loading, error, load } = useCreditsStore();
  const go = useNavStore((s) => s.go);

  const [buying, setBuying] = useState<string | null>(null);
  const [purchaseError, setPurchaseError] = useState<string | null>(null);
  const [toast, setToast] = useState<string | null>(null);

  useEffect(() => {
    load();
  }, [load]);

  const buy = async (packageId: string) => {
    setBuying(packageId);
    setPurchaseError(null);
    setToast(null);
    try {
      const { invoice_link } = await createPurchaseInvoice(packageId);
      const status = await openTelegramInvoice(invoice_link);
      if (status === 'paid') {
        // The bot's SuccessfulPayment handler will grant credits. Wait a
        // beat and re-fetch so the UI shows the new balance.
        await new Promise((r) => setTimeout(r, 800));
        await load();
        await refreshMe();
        setToast(t(lang, 'credits.thank_you'));
      } else if (status === 'failed') {
        setPurchaseError(t(lang, 'credits.purchase_failed'));
      }
      // 'cancelled' / 'pending' — no toast, user can retry.
    } catch (err) {
      setPurchaseError(err instanceof Error ? err.message : 'failed');
    } finally {
      setBuying(null);
    }
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
          <h2 className="step-title">{t(lang, 'credits.title')}</h2>
        </div>

        {error && (
          <div className="glass-card" style={{ padding: 16 }}>
            <span className="error-text">{error}</span>
          </div>
        )}

        {purchaseError && (
          <div className="glass-card" style={{ padding: 16 }}>
            <span className="error-text">{purchaseError}</span>
          </div>
        )}

        {toast && (
          <div className="glass-card" style={{ padding: 16 }}>
            <span style={{ color: 'var(--accent-success)' }}>{toast}</span>
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
                {status.packages.map((p) => {
                  const active = buying === p.id;
                  return (
                    <button
                      key={p.id}
                      className="glass-card credits-package"
                      disabled={buying !== null}
                      onClick={() => buy(p.id)}
                    >
                      <span className="credits-package-label">{p.label}</span>
                      <span className="credits-package-credits">
                        {t(lang, 'credits.credits_amount', {
                          amount: p.credits.toLocaleString(),
                        })}
                      </span>
                      <span className="credits-package-price">
                        {active
                          ? t(lang, 'credits.opening')
                          : t(lang, 'credits.stars_price', { stars: p.stars })}
                      </span>
                    </button>
                  );
                })}
              </div>
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
