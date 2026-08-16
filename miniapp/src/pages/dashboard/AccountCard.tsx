import type { CSSProperties } from 'react';
import { Icon } from '@/components/Icon';
import { formatMoney } from '@/format';
import { t } from '@/i18n';
import { getCurrencyOrFallback } from '@/util/currency';
import type { Account, CurrencyOption, Lang } from '@/types';

type Props = {
  account: Account;
  currencies: CurrencyOption[];
  lang: Lang;
  onEdit: (account: Account) => void;
};

export function AccountCard({ account, currencies, lang, onEdit }: Props) {
  const currency = getCurrencyOrFallback(currencies, account.currency);
  const style = account.color
    ? ({ ['--card-color' as never]: account.color } as CSSProperties)
    : undefined;
  const className = `acct-card${account.color ? '' : ' accent-primary'}`;

  return (
    <button
      type="button"
      className={className}
      style={style}
      onClick={() => onEdit(account)}
      aria-label={account.name}
    >
      <div className="acct-card-top">
        <span className="menu-icon">
          <Icon name={account.icon || 'fa-wallet'} />
        </span>
        <span className="acct-card-name">{account.name}</span>
        <span className="acct-card-type">
          {t(lang, `onboarding.account.type.${account.type}`)}
        </span>
        <span className="acct-card-more" aria-hidden="true">
          <Icon name="fa-ellipsis-vertical" />
        </span>
      </div>
      <div className="acct-card-amount">
        {formatMoney(account.current_balance, currency)}
        <span className="acct-card-currency">{account.currency}</span>
      </div>
      <span className="acct-card-ghost" aria-hidden="true">
        <Icon name={account.icon || 'fa-wallet'} />
      </span>
    </button>
  );
}
