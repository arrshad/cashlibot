import type { CSSProperties, ReactNode } from 'react';
import { Icon } from './Icon';

export type MenuIconTint =
  | 'blue'
  | 'green'
  | 'orange'
  | 'red'
  | 'purple'
  | 'pink'
  | 'teal'
  | 'yellow'
  | 'indigo'
  | 'graphite';

type Props = {
  /** Font Awesome icon name (e.g. "fa-wallet"). */
  name: string;
  /** Semantic tint, or a raw color string for custom backgrounds. */
  tint?: MenuIconTint | string;
  size?: 'sm' | 'lg';
  className?: string;
  children?: ReactNode;
};

const TINT_KEYS: Record<MenuIconTint, string> = {
  blue: 'var(--tint-blue)',
  green: 'var(--tint-green)',
  orange: 'var(--tint-orange)',
  red: 'var(--tint-red)',
  purple: 'var(--tint-purple)',
  pink: 'var(--tint-pink)',
  teal: 'var(--tint-teal)',
  yellow: 'var(--tint-yellow)',
  indigo: 'var(--tint-indigo)',
  graphite: 'var(--tint-graphite)',
};

function resolveTint(tint: MenuIconTint | string | undefined): string | undefined {
  if (!tint) return undefined;
  if (tint in TINT_KEYS) return TINT_KEYS[tint as MenuIconTint];
  return tint;
}

export function MenuIcon({
  name,
  tint = 'graphite',
  size = 'sm',
  className,
}: Props) {
  const style: CSSProperties = { background: resolveTint(tint) };
  return (
    <span
      className={`menu-icon${size === 'lg' ? ' lg' : ''}${className ? ` ${className}` : ''}`}
      style={style}
    >
      <Icon name={name} />
    </span>
  );
}
