import { Icon } from '@/components/Icon';
import { formatMoney } from '@/format';
import { t } from '@/i18n';
import { useAppStore } from '@/store/app';
import { getCurrencyOrFallback } from '@/util/currency';
import { formatDate } from '@/util/format-date';
import type { Account, Category, Transaction } from '@/types';

type Props = {
  tx: Transaction;
  accounts: Account[];
  categories: Category[];
};

const TYPE_FALLBACK_ICON: Record<Transaction['type'], string> = {
  income: 'fa-circle-plus',
  expense: 'fa-circle-minus',
  transfer: 'fa-right-left',
};

const TYPE_ACCENT: Record<Transaction['type'], string> = {
  income: 'var(--accent-success)',
  expense: 'var(--accent-danger)',
  transfer: 'var(--accent-primary)',
};

export function TransactionRow({ tx, accounts, categories }: Props) {
  const me = useAppStore((s) => s.me!);
  const config = useAppStore((s) => s.config!);
  const lang = me.language_code;

  const account = accounts.find((a) => a.id === tx.account_id);
  const toAccount = tx.to_account_id
    ? accounts.find((a) => a.id === tx.to_account_id)
    : null;
  const category = tx.category_id
    ? categories.find((c) => c.id === tx.category_id)
    : null;
  const currency = getCurrencyOrFallback(config.currencies, tx.currency);

  const icon = category?.icon ?? TYPE_FALLBACK_ICON[tx.type];
  const title =
    tx.merchant ||
    tx.description ||
    category?.name ||
    (tx.type === 'transfer'
      ? `${account?.name ?? '?'} → ${toAccount?.name ?? '?'}`
      : t(lang, `dashboard.tx.type.${tx.type}`));

  const sign = tx.type === 'income' ? '+' : tx.type === 'expense' ? '-' : '';
  const amountText = `${sign}${formatMoney(tx.amount, currency)}`;

  const subtitleParts: string[] = [];
  if (account) subtitleParts.push(account.name);
  if (tx.type === 'transfer' && toAccount) subtitleParts.push(`→ ${toAccount.name}`);
  subtitleParts.push(
    formatDate(tx.occurred_at, lang, me.calendar_system, me.timezone, 'short'),
  );

  return (
    <div className="tx-row glass-card">
      <div
        className="tx-row-icon"
        style={{ color: TYPE_ACCENT[tx.type] }}
      >
        <Icon name={icon} size="lg" />
      </div>
      <div className="tx-row-meta">
        <div className="tx-row-title">{title}</div>
        <div className="tx-row-sub">{subtitleParts.join(' · ')}</div>
      </div>
      <div
        className="tx-row-amount"
        style={{ color: TYPE_ACCENT[tx.type] }}
      >
        {amountText}
      </div>
    </div>
  );
}
