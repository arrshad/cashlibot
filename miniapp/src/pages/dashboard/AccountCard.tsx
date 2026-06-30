import { Icon } from '@/components/Icon';
import { formatMoney } from '@/format';
import { t } from '@/i18n';
import { getCurrencyOrFallback } from '@/util/currency';
import type { Account, CurrencyOption, Lang } from '@/types';

type Props = {
  account: Account;
  currencies: CurrencyOption[];
  lang: Lang;
};

export function AccountCard({ account, currencies, lang }: Props) {
  const currency = getCurrencyOrFallback(currencies, account.currency);

  return (
    <div className="account-card glass-card">
      <div
        className="account-card-icon"
        style={{ color: account.color ?? 'var(--accent-primary)' }}
      >
        <Icon name={account.icon} size="lg" />
      </div>
      <div className="account-card-meta">
        <div className="account-card-row">
          <span className="account-card-name">{account.name}</span>
          {account.is_default && (
            <span className="chip">{t(lang, 'dashboard.account.default_chip')}</span>
          )}
        </div>
        <div className="account-card-row account-card-sub">
          <span>{t(lang, `onboarding.account.type.${account.type}`)}</span>
          <span>·</span>
          <span>{account.currency}</span>
        </div>
      </div>
      <div className="account-card-balance">
        {formatMoney(account.current_balance, currency)}
      </div>
    </div>
  );
}
