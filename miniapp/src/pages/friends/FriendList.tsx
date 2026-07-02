import { useEffect, useState } from 'react';
import { Icon } from '@/components/Icon';
import { t } from '@/i18n';
import { useAppStore } from '@/store/app';
import { useFriendsStore } from '@/store/friends';
import { useNavStore } from '@/store/nav';
import type { Friendship } from '@/types';

export function FriendList() {
  const me = useAppStore((s) => s.me!);
  const lang = me.language_code;
  const { overview, loading, error, load, request, accept, decline } =
    useFriendsStore();
  const go = useNavStore((s) => s.go);

  const [showAdd, setShowAdd] = useState(false);
  const [addValue, setAddValue] = useState('');
  const [addBusy, setAddBusy] = useState(false);
  const [addError, setAddError] = useState<string | null>(null);
  const [busyId, setBusyId] = useState<string | null>(null);

  useEffect(() => {
    load();
  }, [load]);

  const submitAdd = async () => {
    const value = addValue.trim();
    if (!value) return;
    setAddBusy(true);
    setAddError(null);
    try {
      await request(value);
      setAddValue('');
      setShowAdd(false);
    } catch (err) {
      // API returns 400 with detail; axios wraps into an AxiosError.
      const msg =
        (err as { response?: { data?: { detail?: string } } })?.response?.data
          ?.detail ??
        (err instanceof Error ? err.message : 'failed');
      setAddError(msg);
    } finally {
      setAddBusy(false);
    }
  };

  const runAction = async (id: string, fn: (id: string) => Promise<void>) => {
    setBusyId(id);
    try {
      await fn(id);
    } finally {
      setBusyId(null);
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
          <h2 className="step-title">{t(lang, 'friends.title')}</h2>
          <button
            className="text-btn"
            style={{ marginInlineStart: 'auto' }}
            onClick={() => setShowAdd((s) => !s)}
          >
            <Icon name="fa-plus" /> {t(lang, 'common.add')}
          </button>
        </div>

        {showAdd && (
          <div className="glass-card" style={{ padding: 14 }}>
            <div className="field">
              <span className="field-label">
                {t(lang, 'friends.add.username_label')}
              </span>
              <input
                className="input"
                placeholder={t(lang, 'friends.add.username_placeholder')}
                value={addValue}
                onChange={(e) => {
                  setAddValue(e.target.value);
                  setAddError(null);
                }}
                autoFocus
              />
              {addError && <span className="error-text">{addError}</span>}
              <div style={{ display: 'flex', gap: 8, marginTop: 8 }}>
                <button
                  className="btn btn-ghost"
                  onClick={() => {
                    setShowAdd(false);
                    setAddValue('');
                    setAddError(null);
                  }}
                >
                  {t(lang, 'common.cancel')}
                </button>
                <button
                  className="btn btn-primary"
                  disabled={addBusy || !addValue.trim()}
                  onClick={submitAdd}
                >
                  {t(lang, 'friends.add.submit')}
                </button>
              </div>
            </div>
          </div>
        )}

        {error && (
          <div className="glass-card" style={{ padding: 16 }}>
            <span className="error-text">{error}</span>
          </div>
        )}

        {loading && !overview && (
          <div className="glass-card" style={{ padding: 16 }}>
            {t(lang, 'common.loading')}
          </div>
        )}

        {overview && (
          <>
            {overview.incoming.length > 0 && (
              <Section title={t(lang, 'friends.section.incoming')}>
                {overview.incoming.map((f) => (
                  <FriendRow key={f.id} f={f}>
                    <button
                      className="text-btn"
                      disabled={busyId === f.id}
                      onClick={() => runAction(f.id, accept)}
                    >
                      {t(lang, 'friends.action.accept')}
                    </button>
                    <button
                      className="text-btn text-btn-danger"
                      disabled={busyId === f.id}
                      onClick={() => runAction(f.id, decline)}
                    >
                      {t(lang, 'friends.action.decline')}
                    </button>
                  </FriendRow>
                ))}
              </Section>
            )}

            <Section
              title={t(lang, 'friends.section.accepted', {
                count: overview.accepted.length,
              })}
            >
              {overview.accepted.length === 0 ? (
                <div className="glass-card" style={{ padding: 16 }}>
                  <span className="hint-text">
                    {t(lang, 'friends.section.accepted_empty')}
                  </span>
                </div>
              ) : (
                overview.accepted.map((f) => (
                  <FriendRow
                    key={f.id}
                    f={f}
                    onOpen={() =>
                      go({
                        name: 'friend-detail',
                        friendId: f.peer.telegram_id,
                      })
                    }
                  />
                ))
              )}
            </Section>

            {overview.outgoing.length > 0 && (
              <Section title={t(lang, 'friends.section.outgoing')}>
                {overview.outgoing.map((f) => (
                  <FriendRow key={f.id} f={f}>
                    <span className="hint-text">
                      {t(lang, 'friends.badge.pending')}
                    </span>
                  </FriendRow>
                ))}
              </Section>
            )}
          </>
        )}
      </div>
    </div>
  );
}

function Section({
  title,
  children,
}: {
  title: string;
  children: React.ReactNode;
}) {
  return (
    <section className="section">
      <div className="section-header">
        <h3 className="section-title">{title}</h3>
      </div>
      <div className="friend-list">{children}</div>
    </section>
  );
}

function FriendRow({
  f,
  children,
  onOpen,
}: {
  f: Friendship;
  children?: React.ReactNode;
  onOpen?: () => void;
}) {
  const clickable = !!onOpen;
  return (
    <div
      className={`glass-card friend-row ${clickable ? 'friend-row-clickable' : ''}`}
      onClick={clickable ? onOpen : undefined}
      role={clickable ? 'button' : undefined}
    >
      <div className="friend-row-body">
        <div className="friend-row-name">{f.peer.display_name}</div>
        {f.peer.username && (
          <div className="friend-row-handle">@{f.peer.username}</div>
        )}
      </div>
      {children && (
        <div
          className="friend-row-actions"
          onClick={(e) => e.stopPropagation()}
        >
          {children}
        </div>
      )}
    </div>
  );
}
