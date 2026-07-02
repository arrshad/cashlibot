import { useEffect, useState } from 'react';
import { adjustCredits, fetchUserDetail } from '../api';
import { useAppStore } from '../store';
import type { UserDetail } from '../types';

function formatDate(iso: string | null): string {
  if (!iso) return '—';
  return new Date(iso).toISOString().replace('T', ' ').split('.')[0] + 'Z';
}

const REASON_LABELS: Record<string, string> = {
  signup_bonus: 'Signup bonus',
  referral_bonus: 'Referral',
  friend_bonus: 'Friend bonus',
  stars_purchase: 'Stars purchase',
  ai_usage: 'AI usage',
  admin_adjustment: 'Admin adjustment',
};

export function UserDetailPage({ userId }: { userId: number }) {
  const go = useAppStore((s) => s.go);
  const [detail, setDetail] = useState<UserDetail | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [change, setChange] = useState('');
  const [reference, setReference] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [toast, setToast] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    fetchUserDetail(userId)
      .then((d) => {
        if (!cancelled) setDetail(d);
      })
      .catch((err) => {
        if (!cancelled) setError(err instanceof Error ? err.message : 'failed');
      });
    return () => {
      cancelled = true;
    };
  }, [userId]);

  const submitAdjust = async () => {
    const value = Number(change);
    if (!Number.isFinite(value) || value === 0) return;
    setSubmitting(true);
    setError(null);
    setToast(null);
    try {
      const updated = await adjustCredits(userId, {
        change: value,
        reference: reference || null,
      });
      setDetail(updated);
      setChange('');
      setReference('');
      setToast(`Balance is now ${updated.credit_balance.toLocaleString()}.`);
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

  if (error && !detail) {
    return (
      <div className="stack">
        <div className="error">{error}</div>
      </div>
    );
  }

  if (!detail) {
    return <div className="card">Loading…</div>;
  }

  return (
    <div className="stack">
      <button
        className="detail-back"
        onClick={() => go({ name: 'users' })}
      >
        ← Back to users
      </button>

      <div className="card">
        <div style={{ display: 'flex', alignItems: 'baseline', gap: 12 }}>
          <h2 style={{ margin: 0 }}>{detail.display_name}</h2>
          <span style={{ color: 'var(--text-tertiary)' }}>
            {detail.username ? `@${detail.username}` : `id ${detail.telegram_id}`}
          </span>
          {detail.is_admin && <span className="chip chip-admin">admin</span>}
        </div>
        <div className="kpi-grid" style={{ marginTop: 16 }}>
          <div style={{ padding: 0 }}>
            <div className="kpi-label">Balance</div>
            <div className="kpi-value">
              {detail.credit_balance.toLocaleString()}
            </div>
          </div>
          <div style={{ padding: 0 }}>
            <div className="kpi-label">Transactions</div>
            <div className="kpi-value">{detail.tx_count.toLocaleString()}</div>
          </div>
          <div style={{ padding: 0 }}>
            <div className="kpi-label">Last activity</div>
            <div className="kpi-value" style={{ fontSize: 14, fontWeight: 500 }}>
              {formatDate(detail.last_tx_at)}
            </div>
          </div>
          <div style={{ padding: 0 }}>
            <div className="kpi-label">Joined</div>
            <div className="kpi-value" style={{ fontSize: 14, fontWeight: 500 }}>
              {formatDate(detail.created_at)}
            </div>
          </div>
        </div>
      </div>

      <div className="card">
        <div className="kpi-label" style={{ marginBottom: 12 }}>Adjust credits</div>
        {toast && (
          <div
            className="error"
            style={{
              background: 'rgba(76, 204, 136, 0.12)',
              borderColor: 'rgba(76, 204, 136, 0.35)',
              color: 'var(--accent-success)',
              marginBottom: 12,
            }}
          >
            {toast}
          </div>
        )}
        {error && <div className="error" style={{ marginBottom: 12 }}>{error}</div>}
        <div className="adjust-form">
          <input
            type="number"
            placeholder="e.g. 50 or -20"
            value={change}
            onChange={(e) => setChange(e.target.value)}
          />
          <input
            placeholder="Reference (optional)"
            value={reference}
            onChange={(e) => setReference(e.target.value)}
            style={{ minWidth: 220 }}
          />
          <button
            disabled={submitting || !change || Number(change) === 0}
            onClick={submitAdjust}
          >
            Apply
          </button>
        </div>
        <p style={{ color: 'var(--text-tertiary)', marginTop: 8, fontSize: 12 }}>
          Positive = grant, negative = deduct. Every change writes a
          <code style={{ margin: '0 4px' }}>credittransaction</code> row with
          reason <code>admin_adjustment</code>.
        </p>
      </div>

      <div className="card">
        <div className="kpi-label" style={{ marginBottom: 12 }}>
          Credit history (last 30)
        </div>
        <div style={{ overflowX: 'auto' }}>
          <table>
            <thead>
              <tr>
                <th>When</th>
                <th>Reason</th>
                <th className="numeric">Δ</th>
                <th className="numeric">Balance</th>
                <th>Reference</th>
              </tr>
            </thead>
            <tbody>
              {detail.credit_history.map((r) => (
                <tr key={r.id} style={{ cursor: 'default' }}>
                  <td>{formatDate(r.created_at)}</td>
                  <td>{REASON_LABELS[r.reason] ?? r.reason}</td>
                  <td
                    className="numeric"
                    style={{
                      color:
                        r.change_amount > 0
                          ? 'var(--accent-success)'
                          : 'var(--accent-danger)',
                    }}
                  >
                    {r.change_amount > 0 ? '+' : ''}
                    {r.change_amount}
                  </td>
                  <td className="numeric">{r.balance_after.toLocaleString()}</td>
                  <td style={{ color: 'var(--text-tertiary)', fontSize: 12 }}>
                    {r.reference_id ?? '—'}
                  </td>
                </tr>
              ))}
              {detail.credit_history.length === 0 && (
                <tr>
                  <td colSpan={5} style={{ padding: 20, color: 'var(--text-tertiary)' }}>
                    No credit activity yet.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
