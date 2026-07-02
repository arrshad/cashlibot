import { useEffect, useMemo, useState } from 'react';
import { Icon } from '@/components/Icon';
import { t } from '@/i18n';
import { useAppStore } from '@/store/app';
import { useFriendsStore } from '@/store/friends';
import { useNavStore } from '@/store/nav';
import { useSharedExpensesStore } from '@/store/sharedExpenses';

type Props = { friendId?: number };

function even(total: number, parts: number, decimals = 2): string {
  if (parts <= 0) return '0';
  return (total / parts).toFixed(decimals);
}

export function AddSharedExpense({ friendId }: Props) {
  const me = useAppStore((s) => s.me!);
  const config = useAppStore((s) => s.config!);
  const overview = useFriendsStore((s) => s.overview);
  const loadFriends = useFriendsStore((s) => s.load);
  const create = useSharedExpensesStore((s) => s.create);
  const go = useNavStore((s) => s.go);
  const lang = me.language_code;

  useEffect(() => {
    if (!overview) loadFriends();
  }, [overview, loadFriends]);

  const friends = overview?.accepted ?? [];

  const [description, setDescription] = useState('');
  const [total, setTotal] = useState('');
  const [currency, setCurrency] = useState(me.default_currency ?? 'USD');
  const [picked, setPicked] = useState<Set<number>>(
    friendId ? new Set([friendId]) : new Set(),
  );
  const [amounts, setAmounts] = useState<Record<number, string>>({});
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const numericTotal = Number(total);
  const totalValid = Number.isFinite(numericTotal) && numericTotal > 0;

  // Whenever the total / selection changes, refresh unset splits to an even
  // share across the picked friends + the creator (parts = picked + 1).
  const evenPerPerson = useMemo(
    () => (totalValid ? even(numericTotal, picked.size + 1) : '0'),
    [totalValid, numericTotal, picked.size],
  );

  const toggle = (uid: number) => {
    setPicked((old) => {
      const next = new Set(old);
      if (next.has(uid)) {
        next.delete(uid);
      } else {
        next.add(uid);
      }
      return next;
    });
  };

  const setAmount = (uid: number, value: string) => {
    setAmounts((a) => ({ ...a, [uid]: value.replace(',', '.') }));
  };

  const canSubmit =
    !submitting &&
    description.trim().length > 0 &&
    totalValid &&
    picked.size > 0 &&
    Array.from(picked).every((uid) => {
      const v = Number(amounts[uid] ?? evenPerPerson);
      return Number.isFinite(v) && v > 0;
    });

  const submit = async () => {
    setSubmitting(true);
    setError(null);
    try {
      await create({
        description: description.trim(),
        total_amount: total.trim(),
        currency,
        splits: Array.from(picked).map((uid) => ({
          user_id: uid,
          amount_owed: (amounts[uid] ?? evenPerPerson).toString(),
        })),
      });
      if (friendId) {
        go({ name: 'friend-detail', friendId });
      } else {
        go({ name: 'friends' });
      }
    } catch (err) {
      const msg =
        (err as { response?: { data?: { detail?: string } } })?.response?.data
          ?.detail ??
        (err instanceof Error ? err.message : 'failed');
      setError(msg);
    } finally {
      setSubmitting(false);
    }
  };

  const backTarget = friendId
    ? ({ name: 'friend-detail', friendId } as const)
    : ({ name: 'friends' } as const);

  return (
    <div className="app-shell">
      <div className="app-frame">
        <div className="glass-card" style={{ padding: 22 }}>
          <div className="step">
            <div className="page-header">
              <button
                className="icon-btn"
                onClick={() => go(backTarget)}
                aria-label={t(lang, 'common.back')}
              >
                <Icon name="fa-arrow-left" />
              </button>
              <h2 className="step-title">{t(lang, 'shared.add_title')}</h2>
            </div>

            <div className="field">
              <span className="field-label">{t(lang, 'shared.add.description')}</span>
              <input
                className="input"
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                placeholder={t(lang, 'shared.add.description_placeholder')}
                maxLength={200}
                autoFocus
              />
            </div>

            <div className="field">
              <span className="field-label">{t(lang, 'shared.add.total')}</span>
              <input
                className="input input-amount"
                inputMode="decimal"
                value={total}
                onChange={(e) => setTotal(e.target.value.replace(',', '.'))}
                placeholder="0"
              />
            </div>

            <div className="field">
              <span className="field-label">
                {t(lang, 'onboarding.account.currency_label')}
              </span>
              <div className="choice-grid">
                {config.currencies.map((c) => (
                  <button
                    key={c.code}
                    className={`btn ${currency === c.code ? 'btn-selected' : ''}`}
                    onClick={() => setCurrency(c.code)}
                  >
                    <span style={{ fontWeight: 600 }}>{c.code}</span>
                    <span
                      style={{ color: 'var(--text-secondary)', marginInlineStart: 8 }}
                    >
                      {c.symbol}
                    </span>
                  </button>
                ))}
              </div>
            </div>

            <div className="field">
              <span className="field-label">{t(lang, 'shared.add.participants')}</span>
              {friends.length === 0 ? (
                <span className="hint-text">
                  {t(lang, 'shared.add.no_friends')}
                </span>
              ) : (
                <div className="choice-grid">
                  {friends.map((f) => (
                    <button
                      key={f.peer.telegram_id}
                      className={`btn ${
                        picked.has(f.peer.telegram_id) ? 'btn-selected' : ''
                      }`}
                      onClick={() => toggle(f.peer.telegram_id)}
                    >
                      {f.peer.display_name}
                    </button>
                  ))}
                </div>
              )}
            </div>

            {picked.size > 0 && (
              <div className="field">
                <span className="field-label">
                  {t(lang, 'shared.add.per_person')}
                </span>
                <p className="hint-text">
                  {t(lang, 'shared.add.per_person_hint', {
                    amount: evenPerPerson,
                  })}
                </p>
                <div className="split-inputs">
                  {Array.from(picked).map((uid) => {
                    const friend = friends.find((f) => f.peer.telegram_id === uid);
                    return (
                      <div key={uid} className="split-input-row">
                        <span className="split-input-name">
                          {friend?.peer.display_name ?? uid}
                        </span>
                        <input
                          className="input"
                          inputMode="decimal"
                          placeholder={evenPerPerson}
                          value={amounts[uid] ?? ''}
                          onChange={(e) => setAmount(uid, e.target.value)}
                        />
                      </div>
                    );
                  })}
                </div>
              </div>
            )}

            {error && <span className="error-text">{error}</span>}

            <div className="step-footer">
              <button className="btn btn-ghost" onClick={() => go(backTarget)}>
                {t(lang, 'common.back')}
              </button>
              <button
                className="btn btn-primary"
                disabled={!canSubmit}
                onClick={submit}
              >
                {t(lang, 'shared.add.submit')}
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
