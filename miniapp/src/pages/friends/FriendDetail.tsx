import { useEffect, useState } from 'react';
import { Icon } from '@/components/Icon';
import { formatMoney } from '@/format';
import { t } from '@/i18n';
import { useAppStore } from '@/store/app';
import { useFriendsStore } from '@/store/friends';
import { useNavStore } from '@/store/nav';
import { useSharedExpensesStore } from '@/store/sharedExpenses';
import { getCurrencyOrFallback } from '@/util/currency';
import type { Lang, SharedExpense } from '@/types';

type Props = { friendId: number };

export function FriendDetail({ friendId }: Props) {
  const me = useAppStore((s) => s.me!);
  const config = useAppStore((s) => s.config!);
  const lang = me.language_code;
  const overview = useFriendsStore((s) => s.overview);
  const loadFriends = useFriendsStore((s) => s.load);
  const balances = useSharedExpensesStore((s) => s.balances);
  const loadBalance = useSharedExpensesStore((s) => s.loadBalance);
  const settle = useSharedExpensesStore((s) => s.settle);
  const go = useNavStore((s) => s.go);

  const [settling, setSettling] = useState(false);
  const [toast, setToast] = useState<string | null>(null);

  const balance = balances[friendId];

  useEffect(() => {
    if (!overview) loadFriends();
    loadBalance(friendId).catch(() => undefined);
  }, [friendId, overview, loadFriends, loadBalance]);

  const peer =
    overview?.accepted.find((f) => f.peer.telegram_id === friendId)?.peer ?? null;

  const doSettle = async () => {
    setSettling(true);
    setToast(null);
    try {
      const count = await settle(friendId);
      setToast(t(lang, 'shared.settle_toast', { count }));
    } finally {
      setSettling(false);
    }
  };

  return (
    <div className="app-shell">
      <div className="app-frame">
        <div className="page-header">
          <button
            className="icon-btn"
            onClick={() => go({ name: 'friends' })}
            aria-label={t(lang, 'common.back')}
          >
            <Icon name="fa-arrow-left" />
          </button>
          <h2 className="step-title">{peer?.display_name ?? '…'}</h2>
        </div>

        {balance && (
          <div className="glass-card balance-card">
            <span className="field-label">{t(lang, 'shared.balance_title')}</span>
            {balance.per_currency.length === 0 ? (
              <span className="hint-text">{t(lang, 'shared.balance_zero')}</span>
            ) : (
              <div className="balance-list">
                {balance.per_currency.map((b) => {
                  const currency = getCurrencyOrFallback(config.currencies, b.currency);
                  const value = Number(b.amount);
                  const positive = value > 0;
                  return (
                    <div key={b.currency} className="balance-row">
                      <span
                        className="balance-row-amount"
                        style={{
                          color: positive
                            ? 'var(--accent-success)'
                            : 'var(--accent-danger)',
                        }}
                      >
                        {positive ? '+' : ''}
                        {formatMoney(b.amount, currency)}
                      </span>
                      <span className="hint-text">
                        {positive
                          ? t(lang, 'shared.owes_you')
                          : t(lang, 'shared.you_owe')}
                      </span>
                    </div>
                  );
                })}
              </div>
            )}
          </div>
        )}

        <div className="friend-detail-actions">
          <button
            className="btn btn-primary"
            onClick={() => go({ name: 'add-shared-expense', friendId })}
          >
            <Icon name="fa-plus" /> {t(lang, 'shared.add_expense')}
          </button>
          <button
            className="btn btn-ghost"
            disabled={
              settling || !balance || balance.per_currency.length === 0
            }
            onClick={doSettle}
          >
            {t(lang, 'shared.settle')}
          </button>
        </div>

        {toast && (
          <div className="glass-card" style={{ padding: 12 }}>
            <span style={{ color: 'var(--accent-success)' }}>{toast}</span>
          </div>
        )}

        <section className="section">
          <div className="section-header">
            <h3 className="section-title">{t(lang, 'shared.expenses_title')}</h3>
          </div>
          {balance && balance.expenses.length === 0 ? (
            <div className="glass-card" style={{ padding: 16 }}>
              <span className="hint-text">{t(lang, 'shared.expenses_empty')}</span>
            </div>
          ) : (
            <div className="reminder-list">
              {balance?.expenses.map((e) => (
                <ExpenseRow
                  key={e.id}
                  expense={e}
                  meId={me.telegram_id}
                  friendId={friendId}
                  lang={lang}
                />
              ))}
            </div>
          )}
        </section>
      </div>
    </div>
  );
}

function ExpenseRow({
  expense,
  meId,
  friendId,
  lang,
}: {
  expense: SharedExpense;
  meId: number;
  friendId: number;
  lang: Lang;
}) {
  const config = useAppStore((s) => s.config!);
  const currency = getCurrencyOrFallback(config.currencies, expense.currency);
  const meCreated = expense.created_by_user_id === meId;
  const affecting = expense.splits.find((s) =>
    meCreated ? s.user_id === friendId : s.user_id === meId,
  );

  return (
    <div className="glass-card reminder-card">
      <div className="reminder-card-body">
        <div className="reminder-card-title">{expense.description}</div>
        <div className="reminder-card-meta">
          <span>
            {t(lang, 'shared.total')} {formatMoney(expense.total_amount, currency)}
          </span>
          {affecting && (
            <>
              <span>·</span>
              <span>
                {t(lang, meCreated ? 'shared.friend_owes' : 'shared.you_owe_row')}:{' '}
                {formatMoney(affecting.amount_owed, currency)}
              </span>
            </>
          )}
          <span>·</span>
          <span className="chip">
            {t(lang, `shared.status.${expense.status}`)}
          </span>
          {affecting && (
            <>
              <span>·</span>
              <span className="chip">
                {t(lang, `shared.split_status.${affecting.status}`)}
              </span>
            </>
          )}
        </div>
      </div>
    </div>
  );
}
