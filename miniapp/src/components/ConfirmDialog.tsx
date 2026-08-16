import { useEffect, useRef, useState } from 'react';

type Props = {
  title?: string;
  message: string;
  confirmLabel: string;
  cancelLabel: string;
  destructive?: boolean;
  onConfirm: () => void;
  onCancel: () => void;
};

const EXIT_MS = 180;

export function ConfirmDialog({
  title,
  message,
  confirmLabel,
  cancelLabel,
  destructive = false,
  onConfirm,
  onCancel,
}: Props) {
  const [closing, setClosing] = useState(false);
  const timerRef = useRef<number | null>(null);

  const finish = (cb: () => void) => {
    if (closing) return;
    setClosing(true);
    timerRef.current = window.setTimeout(cb, EXIT_MS);
  };

  useEffect(
    () => () => {
      if (timerRef.current) window.clearTimeout(timerRef.current);
    },
    [],
  );

  return (
    <div
      className={`confirm-backdrop${closing ? ' is-closing' : ''}`}
      onClick={() => finish(onCancel)}
    >
      <div
        className={`confirm-card${closing ? ' is-closing' : ''}`}
        role="alertdialog"
        aria-modal="true"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="confirm-body">
          {title && <p className="confirm-title">{title}</p>}
          <p className="confirm-message">{message}</p>
        </div>
        <div className="confirm-actions">
          <button
            type="button"
            className="confirm-btn cancel"
            onClick={() => finish(onCancel)}
          >
            {cancelLabel}
          </button>
          <span className="divider" />
          <button
            type="button"
            className={`confirm-btn${destructive ? ' danger' : ''}`}
            onClick={() => finish(onConfirm)}
          >
            {confirmLabel}
          </button>
        </div>
      </div>
    </div>
  );
}
