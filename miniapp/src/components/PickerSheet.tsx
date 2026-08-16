import { Icon } from './Icon';
import { Sheet } from './Sheet';

export type PickerOption<V extends string | number> = {
  value: V;
  label: string;
  hint?: string;
};

type Props<V extends string | number> = {
  title: string;
  value: V;
  options: PickerOption<V>[];
  onChange: (value: V) => void;
  onClose: () => void;
};

export function PickerSheet<V extends string | number>({
  title,
  value,
  options,
  onChange,
  onClose,
}: Props<V>) {
  return (
    <Sheet title={title} onClose={onClose}>
      <div className="picker-list">
        {options.map((opt) => {
          const active = opt.value === value;
          return (
            <button
              key={String(opt.value)}
              className={`picker-row${active ? ' active' : ''}`}
              type="button"
              onClick={() => {
                onChange(opt.value);
                onClose();
              }}
            >
              <span className="picker-row-label">
                {opt.label}
                {opt.hint && (
                  <span className="picker-row-hint">{opt.hint}</span>
                )}
              </span>
              {active && (
                <span className="picker-row-check">
                  <Icon name="fa-check" />
                </span>
              )}
            </button>
          );
        })}
      </div>
    </Sheet>
  );
}
