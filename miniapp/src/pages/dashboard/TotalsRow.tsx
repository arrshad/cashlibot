import { formatMoney } from '@/format';
import { t } from '@/i18n';
import { getCurrencyOrFallback } from '@/util/currency';
import type { CurrencyOption, CurrencyTotal, Lang } from '@/types';

type Props = {
  totals: CurrencyTotal[];
  currencies: CurrencyOption[];
  defaultCurrency: string | null;
  lang: Lang;
};

export function TotalsRow({ totals, currencies, defaultCurrency, lang }: Props) {
  if (totals.length === 0) {
    return (
      <div className="glass-card totals-empty">
        <span className="hint-text">{t(lang, 'dashboard.totals.empty')}</span>
      </div>
    );
  }

  return (
    <div className="totals-row">
      {totals.map((entry) => {
        const currency = getCurrencyOrFallback(currencies, entry.currency);
        const highlighted = entry.currency === defaultCurrency;
        return (
          <div
            key={entry.currency}
            className={`glass-card totals-card ${highlighted ? 'totals-card-primary' : ''}`}
          >
            <span className="totals-card-label">{entry.currency}</span>
            <span className="totals-card-value">
              {formatMoney(entry.amount, currency)}
            </span>
          </div>
        );
      })}
    </div>
  );
}
