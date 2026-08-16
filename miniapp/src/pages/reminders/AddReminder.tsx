import { useMemo, useState } from 'react';
import { Sheet } from '@/components/Sheet';
import { t } from '@/i18n';
import { useAppStore } from '@/store/app';
import { useNavStore } from '@/store/nav';
import { useRemindersStore } from '@/store/reminders';
import type { Frequency, ReminderType } from '@/types';

const TYPES: ReminderType[] = [
  'transaction_log',
  'pay_someone',
  'bill_due',
  'monthly_review',
  'custom',
];

const REPEATS: (Frequency | null)[] = [null, 'daily', 'weekly', 'monthly', 'yearly'];

function defaultDueAtLocal(): string {
  // Default: tomorrow at 9am local. `datetime-local` wants "YYYY-MM-DDTHH:mm".
  const d = new Date();
  d.setDate(d.getDate() + 1);
  d.setHours(9, 0, 0, 0);
  const pad = (n: number) => String(n).padStart(2, '0');
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}T${pad(d.getHours())}:${pad(d.getMinutes())}`;
}

export function AddReminder() {
  const me = useAppStore((s) => s.me!);
  const lang = me.language_code;
  const create = useRemindersStore((s) => s.create);
  const go = useNavStore((s) => s.go);

  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [reminderType, setReminderType] = useState<ReminderType>('custom');
  const [dueAt, setDueAt] = useState<string>(useMemo(defaultDueAtLocal, []));
  const [repeat, setRepeat] = useState<Frequency | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const canSubmit = !submitting && title.trim().length > 0 && dueAt.length > 0;

  const submit = async () => {
    setSubmitting(true);
    setError(null);
    try {
      // Interpret the datetime-local as being in the user's tz. Build an ISO
      // string with the local wall-clock time; the server treats naive input
      // as UTC, which is fine for MVP (the tz picker comes with settings).
      const iso = new Date(dueAt).toISOString();
      await create({
        title: title.trim(),
        description: description.trim() || null,
        reminder_type: reminderType,
        due_at: iso,
        repeat_frequency: repeat,
      });
      go({ name: 'reminders' });
    } catch (err) {
      setError(err instanceof Error ? err.message : 'failed');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <Sheet
      title={t(lang, 'reminder.add.title')}
      onClose={() => go({ name: 'reminders' })}
      footer={
        <button
          className="btn btn-primary"
          disabled={!canSubmit}
          onClick={submit}
        >
          {t(lang, 'reminder.add.submit')}
        </button>
      }
    >
      <div className="field">
        <span className="field-label">{t(lang, 'reminder.add.title_label')}</span>
        <input
          className="input"
          value={title}
          onChange={(e) => setTitle(e.target.value)}
          placeholder={t(lang, 'reminder.add.title_placeholder')}
          maxLength={200}
          autoFocus
        />
      </div>

      <div className="field">
        <span className="field-label">{t(lang, 'reminder.add.due_label')}</span>
        <input
          className="input"
          type="datetime-local"
          value={dueAt}
          onChange={(e) => setDueAt(e.target.value)}
        />
      </div>

      <div className="field">
        <span className="field-label">{t(lang, 'reminder.add.type_label')}</span>
        <div className="choice-grid">
          {TYPES.map((t2) => (
            <button
              key={t2}
              className={`btn ${reminderType === t2 ? 'btn-selected' : ''}`}
              onClick={() => setReminderType(t2)}
            >
              {t(lang, `reminder.type.${t2}`)}
            </button>
          ))}
        </div>
      </div>

      <div className="field">
        <span className="field-label">{t(lang, 'reminder.add.repeat_label')}</span>
        <div className="choice-grid">
          {REPEATS.map((f) => (
            <button
              key={f ?? 'none'}
              className={`btn ${repeat === f ? 'btn-selected' : ''}`}
              onClick={() => setRepeat(f)}
            >
              {f === null
                ? t(lang, 'reminder.frequency.none')
                : t(lang, `reminder.frequency.${f}`)}
            </button>
          ))}
        </div>
      </div>

      <div className="field">
        <span className="field-label">{t(lang, 'reminder.add.description_label')}</span>
        <input
          className="input"
          value={description}
          onChange={(e) => setDescription(e.target.value)}
          maxLength={1000}
        />
      </div>

      {error && <span className="error-text">{error}</span>}
    </Sheet>
  );
}
