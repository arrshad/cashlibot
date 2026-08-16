import { useEffect, useLayoutEffect, useRef, useState, type ReactNode } from 'react';
import { Icon } from './Icon';

export type TabItem<K extends string> = {
  key: K;
  label: string;
  icon: string;
};

type Props<K extends string> = {
  items: TabItem<K>[];
  active: K;
  onSelect: (key: K) => void;
  onFab?: () => void;
  fabIcon?: string;
  fabLabel?: string;
  right?: ReactNode;
};

export function TabBar<K extends string>({
  items,
  active,
  onSelect,
  onFab,
  fabIcon = 'fa-plus',
  fabLabel = 'Add',
  right,
}: Props<K>) {
  const listRef = useRef<HTMLDivElement | null>(null);
  const tabRefs = useRef<Record<string, HTMLButtonElement | null>>({});
  const indicatorRef = useRef<HTMLSpanElement | null>(null);
  const prevIndexRef = useRef<number>(items.findIndex((i) => i.key === active));
  const [indicator, setIndicator] = useState<{ x: number; w: number } | null>(null);
  const [direction, setDirection] = useState<'left' | 'right'>('right');

  const positionIndicator = () => {
    const list = listRef.current;
    const el = tabRefs.current[active];
    if (!list || !el) return;
    const listBox = list.getBoundingClientRect();
    const box = el.getBoundingClientRect();
    setIndicator({ x: box.left - listBox.left, w: box.width });
  };

  useLayoutEffect(() => {
    positionIndicator();
    const nextIndex = items.findIndex((i) => i.key === active);
    const prev = prevIndexRef.current;
    if (nextIndex !== prev) {
      setDirection(nextIndex > prev ? 'right' : 'left');
      prevIndexRef.current = nextIndex;
      const node = indicatorRef.current;
      if (node) {
        node.classList.remove('is-moving');
        void node.offsetWidth;
        node.classList.add('is-moving');
        const t = window.setTimeout(() => node.classList.remove('is-moving'), 620);
        return () => window.clearTimeout(t);
      }
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [active, items.length]);

  useEffect(() => {
    const onResize = () => positionIndicator();
    window.addEventListener('resize', onResize);
    return () => window.removeEventListener('resize', onResize);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return (
    <nav className="tabbar-wrap" aria-label="primary">
      <div className="tabbar" ref={listRef}>
        {indicator && (
          <span
            ref={indicatorRef}
            className="morph-pill"
            data-direction={direction}
            style={{ translate: `${indicator.x}px 0`, width: indicator.w }}
          />
        )}
        {items.map((item) => {
          const isActive = item.key === active;
          return (
            <button
              key={item.key}
              ref={(el) => {
                tabRefs.current[item.key] = el;
              }}
              className={`tabbar-tab${isActive ? ' active' : ''}`}
              onClick={() => onSelect(item.key)}
              aria-current={isActive ? 'page' : undefined}
            >
              <span className="tabbar-tab-glyph">
                <Icon name={item.icon} />
              </span>
              <span>{item.label}</span>
            </button>
          );
        })}
      </div>
      {right ??
        (onFab && (
          <button
            className="tabbar-fab"
            onClick={onFab}
            aria-label={fabLabel}
          >
            <Icon name={fabIcon} />
          </button>
        ))}
    </nav>
  );
}
