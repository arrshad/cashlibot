import {
  type CSSProperties,
  type PointerEvent as ReactPointerEvent,
  type ReactNode,
  useEffect,
  useRef,
  useState,
} from 'react';
import { Icon } from './Icon';

type Props = {
  children: ReactNode;
  onDelete?: () => void;
  className?: string;
  actionWidth?: number;
};

/**
 * Swipe the row left to reveal a red trash bubble at the trailing edge.
 * Committed once the trailing edge crosses `revealThreshold`; snaps closed on
 * click elsewhere.
 */
export function SwipeableRow({
  children,
  onDelete,
  className,
  actionWidth = 60,
}: Props) {
  const revealThreshold = actionWidth * 0.6;
  const [open, setOpen] = useState(false);
  const [dx, setDx] = useState(0);
  const startX = useRef(0);
  const startDx = useRef(0);
  const dragging = useRef(false);
  const containerRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    // Close if the user clicks anywhere outside this row.
    const onDoc = (e: MouseEvent) => {
      if (!open) return;
      if (
        containerRef.current &&
        !containerRef.current.contains(e.target as Node)
      ) {
        setOpen(false);
        setDx(0);
      }
    };
    document.addEventListener('mousedown', onDoc);
    return () => document.removeEventListener('mousedown', onDoc);
  }, [open]);

  const onPointerDown = (e: ReactPointerEvent<HTMLDivElement>) => {
    if (!onDelete) return;
    startX.current = e.clientX;
    startDx.current = open ? -actionWidth : 0;
    dragging.current = true;
    (e.target as HTMLElement).setPointerCapture?.(e.pointerId);
  };

  const onPointerMove = (e: ReactPointerEvent<HTMLDivElement>) => {
    if (!dragging.current) return;
    const delta = e.clientX - startX.current;
    const next = Math.min(0, startDx.current + delta);
    setDx(Math.max(-actionWidth * 1.4, next));
  };

  const finish = () => {
    dragging.current = false;
    if (Math.abs(dx) > revealThreshold) {
      setOpen(true);
      setDx(-actionWidth);
    } else {
      setOpen(false);
      setDx(0);
    }
  };

  const bodyStyle: CSSProperties = { transform: `translateX(${dx}px)` };

  return (
    <div
      ref={containerRef}
      className={`swipe-row${open ? ' is-open' : ''}${className ? ` ${className}` : ''}`}
      onPointerDown={onPointerDown}
      onPointerMove={onPointerMove}
      onPointerUp={finish}
      onPointerCancel={finish}
    >
      <div className="swipe-row-actions" style={{ width: actionWidth }}>
        {onDelete && (
          <button
            type="button"
            className="swipe-row-btn danger"
            onClick={() => {
              setOpen(false);
              setDx(0);
              onDelete();
            }}
            aria-label="Delete"
          >
            <Icon name="fa-trash" />
          </button>
        )}
      </div>
      <div className="swipe-row-body" style={bodyStyle}>
        {children}
      </div>
    </div>
  );
}
