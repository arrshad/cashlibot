import { useEffect, useRef, useState, type ReactNode } from 'react';
import { Icon } from './Icon';

type Props = {
  title: string;
  onClose: () => void;
  children: ReactNode;
  /** Rendered pinned to the bottom of the sheet, always visible. */
  footer?: ReactNode;
  tall?: boolean;
};

const EXIT_MS = 220;

export function Sheet({ title, onClose, children, footer, tall = true }: Props) {
  const [closing, setClosing] = useState(false);
  const timerRef = useRef<number | null>(null);

  const requestClose = () => {
    if (closing) return;
    setClosing(true);
    timerRef.current = window.setTimeout(onClose, EXIT_MS);
  };

  useEffect(
    () => () => {
      if (timerRef.current) window.clearTimeout(timerRef.current);
    },
    [],
  );

  return (
    <div
      className={`sheet-backdrop${closing ? ' is-closing' : ''}`}
      onClick={requestClose}
    >
      <div
        className={`sheet${tall ? ' sheet-tall' : ''}${closing ? ' is-closing' : ''}`}
        role="dialog"
        aria-modal="true"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="sheet-header">
          <button
            type="button"
            className="sheet-close"
            onClick={requestClose}
            aria-label="Close"
          >
            <Icon name="fa-xmark" />
          </button>
          <span className="sheet-title">{title}</span>
          <span className="sheet-header-spacer" aria-hidden="true" />
        </div>
        <div className="sheet-body">{children}</div>
        {footer && <div className="sheet-footer">{footer}</div>}
      </div>
    </div>
  );
}
