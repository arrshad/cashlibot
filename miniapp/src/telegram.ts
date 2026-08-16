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

export type InvoiceStatus = 'paid' | 'cancelled' | 'failed' | 'pending';

type TelegramWebApp = {
  initData: string;
  themeParams: TelegramTheme;
  colorScheme: 'light' | 'dark';
  ready: () => void;
  expand: () => void;
  close: () => void;
  openInvoice?: (url: string, callback?: (status: InvoiceStatus) => void) => void;
};

declare global {
  interface Window {
    Telegram?: { WebApp?: TelegramWebApp };
  }
}

function installDevMock(): void {
  if (!import.meta.env.DEV) return;
  if (window.Telegram?.WebApp?.initData) return;
  const user = { id: 1000000, first_name: 'Dev', language_code: 'en' };
  const authDate = Math.floor(Date.now() / 1000);
  const initData =
    `user=${encodeURIComponent(JSON.stringify(user))}` +
    `&auth_date=${authDate}` +
    `&hash=dev`;
  window.Telegram = {
    WebApp: {
      initData,
      themeParams: {},
      colorScheme: 'dark',
      ready: () => {},
      expand: () => {},
      close: () => {},
    },
  };
}

// Fire at module load so the mock is in place before React first renders.
installDevMock();

export function getTelegramWebApp(): TelegramWebApp | undefined {
  installDevMock();
  return window.Telegram?.WebApp;
}

export function getInitDataRaw(): string {
  return getTelegramWebApp()?.initData ?? '';
}

export function notifyReady(): void {
  getTelegramWebApp()?.ready();
  getTelegramWebApp()?.expand();
}

/**
 * Opens the Telegram Stars payment sheet with the given invoice URL.
 * Resolves once the payment sheet closes with a terminal status.
 * Rejects if the client can't handle invoices (older Telegram version).
 */
export function openTelegramInvoice(url: string): Promise<InvoiceStatus> {
  const tg = getTelegramWebApp();
  return new Promise((resolve, reject) => {
    if (!tg || typeof tg.openInvoice !== 'function') {
      reject(new Error('openInvoice not supported by this Telegram client'));
      return;
    }
    tg.openInvoice(url, (status) => resolve(status));
  });
}
