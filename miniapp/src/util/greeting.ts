import type { Lang } from '@/types';

type Slot = 'morning' | 'afternoon' | 'evening' | 'night' | 'any';

function slot(now: Date): Slot {
  const h = now.getHours();
  if (h < 5) return 'night';
  if (h < 12) return 'morning';
  if (h < 17) return 'afternoon';
  if (h < 22) return 'evening';
  return 'night';
}

const BANK: Record<Lang, Record<Slot, string[]>> = {
  en: {
    morning: ['Good morning', 'Rise and log', 'Fresh start'],
    afternoon: ["Let's check in", 'Good afternoon', 'Keep it up'],
    evening: ['Good evening', 'Wrap the day', 'End on a high'],
    night: ['Good night', 'Late one?', 'Still here?'],
    any: ["Let's do this", 'Hey there', 'Nice to see you'],
  },
  fa: {
    morning: ['صبح بخیر', 'روزت خوب', 'شروع تازه'],
    afternoon: ['وقت بخیر', 'ادامه بده', 'همینو نگه دار'],
    evening: ['عصر بخیر', 'روزتو جمع کن', 'کارت خوب بود'],
    night: ['شب بخیر', 'دیر وقت؟', 'هنوز بیداری؟'],
    any: ['بریم', 'سلام', 'خوش اومدی'],
  },
};

export function pickGreeting(lang: Lang, now: Date = new Date()): string {
  const s = slot(now);
  const pool = BANK[lang][s].concat(BANK[lang].any);
  const seed =
    now.getFullYear() * 10000 +
    (now.getMonth() + 1) * 100 +
    now.getDate() +
    s.length * 7;
  return pool[seed % pool.length];
}
