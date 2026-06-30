import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { resolveIcon } from '@/icons';

type Props = {
  name: string | null | undefined;
  size?: 'sm' | 'md' | 'lg';
  color?: string;
  fixedWidth?: boolean;
};

const SIZES: Record<NonNullable<Props['size']>, string> = {
  sm: '12px',
  md: '16px',
  lg: '20px',
};

export function Icon({ name, size = 'md', color, fixedWidth = true }: Props) {
  return (
    <FontAwesomeIcon
      icon={resolveIcon(name)}
      style={{ fontSize: SIZES[size], color }}
      fixedWidth={fixedWidth}
    />
  );
}
