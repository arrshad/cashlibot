/**
 * Thin typed wrapper over `window.Telegram.WebApp`.
 *
 * Telegram injects this object whenever the page is opened from inside the
 * Telegram client. When opened in a regular browser (e.g. local dev without
 * a tunnel), it's undefined and `initData` is empty.
 */

type TelegramTheme = {
  bg_color?: string;
  text_color?: string;
  hint_color?: string;
};

type TelegramWebApp = {
  initData: string;
  themeParams: TelegramTheme;
  colorScheme: 'light' | 'dark';
  ready: () => void;
  expand: () => void;
  close: () => void;
};

declare global {
  interface Window {
    Telegram?: { WebApp?: TelegramWebApp };
  }
}

export function getTelegramWebApp(): TelegramWebApp | undefined {
  return window.Telegram?.WebApp;
}

export function getInitDataRaw(): string {
  return getTelegramWebApp()?.initData ?? '';
}

export function notifyReady(): void {
  getTelegramWebApp()?.ready();
  getTelegramWebApp()?.expand();
}
