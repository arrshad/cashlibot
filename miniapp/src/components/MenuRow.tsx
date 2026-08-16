import type { ReactNode } from 'react';
import { Icon } from './Icon';
import type { MenuIconTint } from './MenuIcon';

type Props = {
  icon: string;
  tint: MenuIconTint;
  title: string;
  value?: ReactNode;
  onClick?: () => void;
  chevron?: boolean;
};

/**
 * A grouped-list row: gradient-icon square + title + trailing value + chevron.
 * Rows come pre-styled to be stacked inside a .list-section container.
 */
export function MenuRow({
  icon,
  tint,
  title,
  value,
  onClick,
  chevron = true,
}: Props) {
  return (
    <button className="menu-row" onClick={onClick} type="button">
      <span className={`menu-icon-grad menu-icon-grad-${tint}`}>
        <Icon name={icon} />
      </span>
      <span className="menu-row-title">{title}</span>
      {value != null && <span className="menu-row-value">{value}</span>}
      {chevron && (
        <span className="menu-row-chev" aria-hidden="true">
          <Icon name="fa-chevron-right" />
        </span>
      )}
    </button>
  );
}
