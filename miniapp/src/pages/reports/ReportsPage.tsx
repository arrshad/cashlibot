import { useEffect, useMemo } from 'react';
import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Legend,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';
import { Icon } from '@/components/Icon';
import { formatMoney } from '@/format';
import { t } from '@/i18n';
import { useAppStore } from '@/store/app';
import { useNavStore } from '@/store/nav';
import { useReportsStore } from '@/store/reports';
import { getCurrencyOrFallback } from '@/util/currency';
import type {
  BehaviorScore,
  CategoryReportRow,
  Lang,
  MonthBucket,
  ReportPeriod,
} from '@/types';

const PERIODS: ReportPeriod[] = ['week', 'month', 'quarter', 'year'];

const CHART_COLORS = [
  '#7c6ef5',
  '#3ecfb2',
  '#f5a623',
  '#f0606a',
  '#4ccc88',
  '#8ec5fc',
  '#e0aaff',
  '#ffdd80',
  '#5eead4',
  '#fca5a5',
];

const MONTH_LABELS = [
  'Jan',
  'Feb',
  'Mar',
  'Apr',
  'May',
  'Jun',
  'Jul',
  'Aug',
  'Sep',
  'Oct',
  'Nov',
  'Dec',
];

export function ReportsPage() {
  const me = useAppStore((s) => s.me!);
  const lang = me.language_code;
  const { summary, period, loading, error, load } = useReportsStore();
  const go = useNavStore((s) => s.go);

  useEffect(() => {
    load();
  }, [load]);

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
          <h2 className="step-title">{t(lang, 'reports.title')}</h2>
        </div>

        <div className="dashboard-links">
          {PERIODS.map((p) => (
            <button
              key={p}
              className={`btn ${period === p ? 'btn-selected' : 'btn-ghost'}`}
              onClick={() => load(p)}
            >
              {t(lang, `reports.period.${p}`)}
            </button>
          ))}
        </div>

        {error && (
          <div className="glass-card" style={{ padding: 16 }}>
            <span className="error-text">{error}</span>
          </div>
        )}

        {loading && !summary && (
          <div className="glass-card" style={{ padding: 16 }}>
            {t(lang, 'common.loading')}
          </div>
        )}

        {summary && (
          <>
            <BehaviorCard score={summary.behavior_score} lang={lang} />
            <MonthlyDeltaCard summary={summary} lang={lang} />
            <CategoryBreakdownCard rows={summary.by_category} lang={lang} />
            <TrendCard trend={summary.monthly_trend} lang={lang} />
          </>
        )}
      </div>
    </div>
  );
}

function BehaviorCard({
  score,
  lang,
}: {
  score: BehaviorScore;
  lang: Lang;
}) {
  const components: Array<{ label: string; value: number; max: number }> = [
    {
      label: t(lang, 'reports.behavior.logging'),
      value: score.logging_consistency,
      max: 30,
    },
    {
      label: t(lang, 'reports.behavior.budget'),
      value: score.budget_adherence,
      max: 25,
    },
    {
      label: t(lang, 'reports.behavior.savings'),
      value: score.savings_rate,
      max: 25,
    },
    {
      label: t(lang, 'reports.behavior.debt_free'),
      value: score.debt_free,
      max: 10,
    },
    {
      label: t(lang, 'reports.behavior.goal'),
      value: score.goal_progress,
      max: 10,
    },
  ];

  return (
    <div className="glass-card behavior-card">
      <div className="behavior-card-header">
        <span className="field-label">{t(lang, 'reports.behavior.title')}</span>
        <span className="behavior-total">{score.total}</span>
      </div>
      <div className="behavior-breakdown">
        {components.map((c) => {
          const ratio = c.max > 0 ? c.value / c.max : 0;
          return (
            <div key={c.label} className="behavior-row">
              <div className="behavior-row-label">
                <span>{c.label}</span>
                <span className="hint-text">
                  {c.value} / {c.max}
                </span>
              </div>
              <div className="behavior-bar">
                <div
                  className="behavior-bar-fill"
                  style={{
                    width: `${Math.min(100, ratio * 100)}%`,
                    background:
                      ratio >= 0.8
                        ? 'var(--accent-success)'
                        : ratio >= 0.5
                        ? 'var(--accent-warning)'
                        : 'var(--accent-danger)',
                  }}
                />
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

function MonthlyDeltaCard({
  summary,
  lang,
}: {
  summary: import('@/types').ReportSummary;
  lang: Lang;
}) {
  const config = useAppStore((s) => s.config!);
  const cmp = summary.monthly_comparison;
  const currency = cmp.currency
    ? getCurrencyOrFallback(config.currencies, cmp.currency)
    : null;
  const savingsPct = Math.round(summary.savings_rate * 100);

  return (
    <div className="glass-card behavior-card">
      <div className="behavior-card-header">
        <span className="field-label">
          {t(lang, 'reports.monthly.title')}
        </span>
      </div>
      <div className="report-stats">
        {currency && (
          <div className="report-stat">
            <span className="hint-text">{t(lang, 'reports.monthly.this_month')}</span>
            <span className="report-stat-value">
              {formatMoney(cmp.this_month_expense, currency)}
            </span>
          </div>
        )}
        {currency && (
          <div className="report-stat">
            <span className="hint-text">{t(lang, 'reports.monthly.last_month')}</span>
            <span className="report-stat-value">
              {formatMoney(cmp.last_month_expense, currency)}
            </span>
          </div>
        )}
        {cmp.delta_pct !== null && (
          <div className="report-stat">
            <span className="hint-text">{t(lang, 'reports.monthly.change')}</span>
            <span
              className="report-stat-value"
              style={{
                color:
                  cmp.delta_pct > 0
                    ? 'var(--accent-danger)'
                    : 'var(--accent-success)',
              }}
            >
              {cmp.delta_pct > 0 ? '+' : ''}
              {Math.round(cmp.delta_pct * 100)}%
            </span>
          </div>
        )}
        <div className="report-stat">
          <span className="hint-text">{t(lang, 'reports.monthly.savings_rate')}</span>
          <span className="report-stat-value">{savingsPct}%</span>
        </div>
      </div>
    </div>
  );
}

function CategoryBreakdownCard({
  rows,
  lang,
}: {
  rows: CategoryReportRow[];
  lang: Lang;
}) {
  const config = useAppStore((s) => s.config!);
  const chartData = useMemo(
    () =>
      rows.slice(0, 8).map((r, i) => ({
        name: r.name,
        value: Number(r.amount),
        currency: r.currency,
        color: CHART_COLORS[i % CHART_COLORS.length],
      })),
    [rows],
  );

  if (chartData.length === 0) {
    return (
      <div className="glass-card" style={{ padding: 16 }}>
        <span className="field-label">{t(lang, 'reports.by_category.title')}</span>
        <p className="hint-text" style={{ marginTop: 8 }}>
          {t(lang, 'reports.by_category.empty')}
        </p>
      </div>
    );
  }

  return (
    <div className="glass-card behavior-card">
      <div className="behavior-card-header">
        <span className="field-label">{t(lang, 'reports.by_category.title')}</span>
      </div>
      <div style={{ width: '100%', height: 220 }}>
        <ResponsiveContainer>
          <PieChart>
            <Pie
              data={chartData}
              dataKey="value"
              nameKey="name"
              cx="50%"
              cy="50%"
              innerRadius={50}
              outerRadius={90}
              stroke="rgba(255,255,255,0.06)"
            >
              {chartData.map((d, i) => (
                <Cell key={i} fill={d.color} />
              ))}
            </Pie>
            <Tooltip
              contentStyle={{
                background: 'rgba(20,20,35,0.95)',
                border: '1px solid rgba(255,255,255,0.12)',
                borderRadius: 12,
              }}
              formatter={(value: number, _name, item) => {
                const currency = getCurrencyOrFallback(
                  config.currencies,
                  (item.payload as { currency: string }).currency,
                );
                return formatMoney(String(value), currency);
              }}
            />
          </PieChart>
        </ResponsiveContainer>
      </div>
      <div className="category-legend">
        {chartData.map((d) => (
          <div key={d.name} className="category-legend-row">
            <span
              className="category-legend-swatch"
              style={{ background: d.color }}
            />
            <span className="category-legend-name">{d.name}</span>
            <span className="category-legend-value">
              {formatMoney(
                String(d.value),
                getCurrencyOrFallback(config.currencies, d.currency),
              )}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}

function TrendCard({ trend, lang }: { trend: MonthBucket[]; lang: Lang }) {
  const data = trend.map((b) => ({
    label: MONTH_LABELS[b.month - 1],
    income: Number(b.income),
    expense: Number(b.expense),
  }));
  if (data.every((d) => d.income === 0 && d.expense === 0)) {
    return (
      <div className="glass-card" style={{ padding: 16 }}>
        <span className="field-label">{t(lang, 'reports.trend.title')}</span>
        <p className="hint-text" style={{ marginTop: 8 }}>
          {t(lang, 'reports.trend.empty')}
        </p>
      </div>
    );
  }

  return (
    <div className="glass-card behavior-card">
      <div className="behavior-card-header">
        <span className="field-label">{t(lang, 'reports.trend.title')}</span>
      </div>
      <div style={{ width: '100%', height: 220 }}>
        <ResponsiveContainer>
          <BarChart data={data}>
            <CartesianGrid stroke="rgba(255,255,255,0.06)" strokeDasharray="3 3" />
            <XAxis
              dataKey="label"
              stroke="rgba(255,255,255,0.28)"
              tick={{ fill: 'rgba(255,255,255,0.45)', fontSize: 11 }}
            />
            <YAxis
              stroke="rgba(255,255,255,0.28)"
              tick={{ fill: 'rgba(255,255,255,0.45)', fontSize: 11 }}
            />
            <Tooltip
              contentStyle={{
                background: 'rgba(20,20,35,0.95)',
                border: '1px solid rgba(255,255,255,0.12)',
                borderRadius: 12,
              }}
            />
            <Legend wrapperStyle={{ color: 'rgba(255,255,255,0.6)' }} />
            <Bar
              dataKey="income"
              name={t(lang, 'reports.trend.income')}
              fill="#4ccc88"
              radius={[6, 6, 0, 0]}
            />
            <Bar
              dataKey="expense"
              name={t(lang, 'reports.trend.expense')}
              fill="#f0606a"
              radius={[6, 6, 0, 0]}
            />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
