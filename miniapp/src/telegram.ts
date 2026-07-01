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
