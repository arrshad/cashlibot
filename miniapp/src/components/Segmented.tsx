import { useEffect, useLayoutEffect, useRef, useState } from 'react';

export type SegmentedOption<V extends string> = {
  value: V;
  label: string;
};

type Props<V extends string> = {
  options: SegmentedOption<V>[];
  value: V;
  onChange: (value: V) => void;
  className?: string;
};

export function Segmented<V extends string>({
  options,
  value,
  onChange,
  className,
}: Props<V>) {
  const listRef = useRef<HTMLDivElement | null>(null);
  const btnRefs = useRef<Record<string, HTMLButtonElement | null>>({});
  const indicatorRef = useRef<HTMLSpanElement | null>(null);
  const prevIndexRef = useRef<number>(options.findIndex((o) => o.value === value));
  const [pill, setPill] = useState<{ x: number; w: number } | null>(null);
  const [direction, setDirection] = useState<'left' | 'right'>('right');

  const measure = () => {
    const list = listRef.current;
    const el = btnRefs.current[value];
    if (!list || !el) return;
    const listBox = list.getBoundingClientRect();
    const box = el.getBoundingClientRect();
    setPill({ x: box.left - listBox.left, w: box.width });
  };

  useLayoutEffect(() => {
    measure();
    const nextIndex = options.findIndex((o) => o.value === value);
    const prev = prevIndexRef.current;
    if (nextIndex !== prev) {
      setDirection(nextIndex > prev ? 'right' : 'left');
      prevIndexRef.current = nextIndex;
      const node = indicatorRef.current;
      if (node) {
        node.classList.remove('is-moving');
        void node.offsetWidth;
        node.classList.add('is-moving');
        const t = window.setTimeout(
          () => node.classList.remove('is-moving'),
          620,
        );
        return () => window.clearTimeout(t);
      }
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [value, options.length]);

  useEffect(() => {
    const onResize = () => measure();
    window.addEventListener('resize', onResize);
    return () => window.removeEventListener('resize', onResize);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return (
    <div
      className={`segmented${className ? ` ${className}` : ''}`}
      ref={listRef}
    >
      {pill && (
        <span
          ref={indicatorRef}
          className="morph-pill"
          data-direction={direction}
          style={{ translate: `${pill.x}px 0`, width: pill.w }}
        />
      )}
      {options.map((opt) => (
        <button
          key={opt.value}
          ref={(el) => {
            btnRefs.current[opt.value] = el;
          }}
          className={`segmented-opt${opt.value === value ? ' active' : ''}`}
          onClick={() => onChange(opt.value)}
          type="button"
        >
          {opt.label}
        </button>
      ))}
    </div>
  );
}
