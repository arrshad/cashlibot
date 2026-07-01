import { useEffect } from 'react';
import { Icon } from '@/components/Icon';
import { t } from '@/i18n';
import { useAppStore } from '@/store/app';
import { useGamificationStore } from '@/store/gamification';
import { useNavStore } from '@/store/nav';
import type { BadgeStatus } from '@/types';

export function StatsPage() {
  const me = useAppStore((s) => s.me!);
  const lang = me.language_code;
  const { status, loading, error, load } = useGamificationStore();
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
          <h2 className="step-title">{t(lang, 'stats.title')}</h2>
        </div>

        {error && (
          <div className="glass-card" style={{ padding: 16 }}>
            <span className="error-text">{error}</span>
          </div>
        )}

        {loading && !status && (
          <div className="glass-card" style={{ padding: 16 }}>
            {t(lang, 'common.loading')}
          </div>
        )}

        {status && (
          <>
            <div className="glass-card level-card">
              <div className="level-card-row">
                <span className="level-card-label">
                  {t(lang, 'stats.level_label')}
                </span>
                <span className="level-card-value">{status.level}</span>
              </div>
              <div className="level-progress">
                <div
                  className="level-progress-fill"
                  style={{
                    width: `${
                      status.xp_for_level > 0
                        ? Math.min(100, (status.xp_into_level / status.xp_for_level) * 100)
                        : 0
                    }%`,
                  }}
                />
              </div>
              <div className="hint-text">
                {status.xp_into_level} / {status.xp_for_level} XP ·{' '}
                {t(lang, 'stats.total_xp', { xp: status.total_xp })}
              </div>
            </div>

            <section className="section">
              <div className="section-header">
                <h3 className="section-title">{t(lang, 'stats.streaks_title')}</h3>
              </div>
              {status.streaks.length === 0 ? (
                <div className="glass-card" style={{ padding: 16 }}>
                  <span className="hint-text">{t(lang, 'stats.streaks_empty')}</span>
                </div>
              ) : (
                <div className="streak-grid">
                  {status.streaks.map((s) => (
                    <div key={s.streak_type} className="glass-card streak-card">
                      <Icon name="fa-fire" size="lg" color="var(--accent-warning)" />
                      <div className="streak-card-body">
                        <span className="streak-card-value">{s.current_count}</span>
                        <span className="streak-card-label">
                          {t(lang, `stats.streak.${s.streak_type}`)}
                        </span>
                        <span className="hint-text">
                          {t(lang, 'stats.streak_best', { count: s.best_count })}
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </section>

            <section className="section">
              <div className="section-header">
                <h3 className="section-title">{t(lang, 'stats.badges_title')}</h3>
              </div>
              <div className="badge-grid">
                {status.badges.map((b) => (
                  <BadgeTile key={b.id} badge={b} lang={lang} />
                ))}
              </div>
            </section>
          </>
        )}
      </div>
    </div>
  );
}

function BadgeTile({ badge, lang }: { badge: BadgeStatus; lang: 'en' | 'fa' }) {
  const name = lang === 'fa' && badge.name_fa ? badge.name_fa : badge.name;
  const desc =
    lang === 'fa' && badge.description_fa
      ? badge.description_fa
      : badge.description;

  return (
    <div className={`glass-card badge-tile ${badge.earned ? 'badge-earned' : 'badge-locked'}`}>
      <div className="badge-tile-icon">
        <Icon name={badge.icon} size="lg" />
      </div>
      <div className="badge-tile-body">
        <span className="badge-tile-name">{name}</span>
        <span className="badge-tile-desc">{desc}</span>
      </div>
    </div>
  );
}
