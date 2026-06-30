import { t } from '@/i18n';
import { useAppStore } from '@/store/app';

type Props = {
  message: string;
  onRetry: () => void;
};

export function ErrorView({ message, onRetry }: Props) {
  const lang = useAppStore((s) => s.me?.language_code ?? 'en');
  return (
    <div className="status-screen">
      <div className="glass-card">
        <p className="error-text">{message}</p>
        <p className="hint-text" style={{ marginTop: 8 }}>
          {t(lang, 'auth.failed')}
        </p>
        <button className="btn btn-primary" style={{ marginTop: 16 }} onClick={onRetry}>
          {t(lang, 'common.retry')}
        </button>
      </div>
    </div>
  );
}
