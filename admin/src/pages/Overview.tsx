import { useEffect } from 'react';
import { useAppStore } from '../store';

function formatNumber(n: number): string {
  return n.toLocaleString();
}

export function Overview() {
  const overview = useAppStore((s) => s.overview);
  const load = useAppStore((s) => s.loadOverview);
  const loading = useAppStore((s) => s.overviewLoading);
  const error = useAppStore((s) => s.overviewError);

  useEffect(() => {
    load();
  }, [load]);

  return (
    <div className="stack">
      {error && error !== 'unauthorized' && (
        <div className="error">{error}</div>
      )}
      {loading && !overview && (
        <div className="card">Loading…</div>
      )}
      {overview && (
        <>
          <div className="kpi-grid">
            <div className="card kpi">
              <div className="kpi-label">Total users</div>
              <div className="kpi-value">{formatNumber(overview.total_users)}</div>
              <div className="kpi-hint">{overview.admins} admins</div>
            </div>
            <div className="card kpi">
              <div className="kpi-label">DAU / WAU / MAU</div>
              <div className="kpi-value">
                {overview.dau} · {overview.wau} · {overview.mau}
              </div>
              <div className="kpi-hint">Distinct tx-writing users</div>
            </div>
            <div className="card kpi">
              <div className="kpi-label">Credits in circulation</div>
              <div className="kpi-value">
                {formatNumber(overview.credits_in_circulation)}
              </div>
              <div className="kpi-hint">Sum of user balances</div>
            </div>
            <div className="card kpi">
              <div className="kpi-label">AI spend this month</div>
              <div className="kpi-value" style={{ color: 'var(--accent-danger)' }}>
                {formatNumber(overview.ai_credits_spent_this_month)}
              </div>
              <div className="kpi-hint">Credits deducted</div>
            </div>
          </div>

          <div className="card">
            <div className="kpi-label" style={{ marginBottom: 12 }}>
              Telegram Stars — this month
            </div>
            <div className="kpi-grid">
              <div className="kpi" style={{ padding: 0 }}>
                <div className="kpi-label">Purchases</div>
                <div className="kpi-value">
                  {formatNumber(overview.stars_purchases_this_month)}
                </div>
              </div>
              <div className="kpi" style={{ padding: 0 }}>
                <div className="kpi-label">Stars revenue</div>
                <div className="kpi-value" style={{ color: 'var(--accent-warning)' }}>
                  {formatNumber(overview.stars_revenue_this_month)} ⭐
                </div>
              </div>
              <div className="kpi" style={{ padding: 0 }}>
                <div className="kpi-label">Credits granted</div>
                <div className="kpi-value" style={{ color: 'var(--accent-success)' }}>
                  {formatNumber(overview.credits_granted_via_stars_this_month)}
                </div>
              </div>
              <div className="kpi" style={{ padding: 0 }}>
                <div className="kpi-label">Credits / Star</div>
                <div className="kpi-value">
                  {overview.stars_revenue_this_month > 0
                    ? (
                        overview.credits_granted_via_stars_this_month /
                        overview.stars_revenue_this_month
                      ).toFixed(2)
                    : '—'}
                </div>
              </div>
            </div>
          </div>
        </>
      )}
    </div>
  );
}
