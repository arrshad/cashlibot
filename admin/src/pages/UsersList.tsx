import { useEffect, useState } from 'react';
import { fetchUsers } from '../api';
import { useAppStore } from '../store';
import type { UserList } from '../types';

const PAGE_SIZE = 50;

function formatDate(iso: string | null): string {
  if (!iso) return '—';
  const d = new Date(iso);
  return d.toISOString().split('T')[0];
}

export function UsersList() {
  const go = useAppStore((s) => s.go);
  const [data, setData] = useState<UserList | null>(null);
  const [query, setQuery] = useState('');
  const [offset, setOffset] = useState(0);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setError(null);
    fetchUsers(query, offset, PAGE_SIZE)
      .then((next) => {
        if (!cancelled) setData(next);
      })
      .catch((err) => {
        if (!cancelled) {
          setError(err instanceof Error ? err.message : 'failed');
        }
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [query, offset]);

  const totalPages = data ? Math.max(1, Math.ceil(data.total / PAGE_SIZE)) : 1;
  const currentPage = Math.floor(offset / PAGE_SIZE) + 1;

  return (
    <div className="stack">
      <div className="card">
        <div className="search">
          <input
            placeholder="Search by @username or display name…"
            value={query}
            onChange={(e) => {
              setQuery(e.target.value);
              setOffset(0);
            }}
          />
        </div>

        {error && <div className="error">{error}</div>}

        <div style={{ overflowX: 'auto' }}>
          <table>
            <thead>
              <tr>
                <th>User</th>
                <th>Language</th>
                <th>Currency</th>
                <th className="numeric">Credits</th>
                <th className="numeric">Txs</th>
                <th>Last tx</th>
                <th>Joined</th>
                <th>Status</th>
              </tr>
            </thead>
            <tbody>
              {(data?.rows ?? []).map((u) => (
                <tr
                  key={u.telegram_id}
                  onClick={() => go({ name: 'user', userId: u.telegram_id })}
                >
                  <td>
                    <div style={{ fontWeight: 600 }}>{u.display_name}</div>
                    <div style={{ color: 'var(--text-tertiary)', fontSize: 12 }}>
                      {u.username ? `@${u.username}` : `id ${u.telegram_id}`}
                    </div>
                  </td>
                  <td>{u.language_code}</td>
                  <td>{u.default_currency ?? '—'}</td>
                  <td className="numeric">{u.credit_balance.toLocaleString()}</td>
                  <td className="numeric">{u.tx_count}</td>
                  <td>{formatDate(u.last_tx_at)}</td>
                  <td>{formatDate(u.created_at)}</td>
                  <td>
                    {u.is_admin && <span className="chip chip-admin">admin</span>}
                    {!u.onboarding_completed && (
                      <span className="chip chip-off" style={{ marginInlineStart: 4 }}>
                        pending setup
                      </span>
                    )}
                    {u.is_admin || !u.onboarding_completed ? null : (
                      <span className="chip">active</span>
                    )}
                  </td>
                </tr>
              ))}
              {data && data.rows.length === 0 && !loading && (
                <tr>
                  <td colSpan={8} style={{ padding: 20, color: 'var(--text-tertiary)' }}>
                    No users matched.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>

        {data && (
          <div className="pagination">
            <span>
              {data.total.toLocaleString()} users · page {currentPage} of {totalPages}
            </span>
            <div style={{ display: 'flex', gap: 8 }}>
              <button
                disabled={offset === 0 || loading}
                onClick={() => setOffset(Math.max(0, offset - PAGE_SIZE))}
              >
                Previous
              </button>
              <button
                disabled={offset + PAGE_SIZE >= data.total || loading}
                onClick={() => setOffset(offset + PAGE_SIZE)}
              >
                Next
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
