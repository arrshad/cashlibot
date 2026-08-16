const SELECTOR = '.btn, .credit-chip, .tabbar-fab, .icon-btn, .text-btn, .credits-package, .sheet-close';

let installed = false;

export function installSpotlight(): void {
  if (installed) return;
  installed = true;

  const handler = (e: PointerEvent) => {
    const target = e.target;
    if (!(target instanceof Element)) return;
    const el = target.closest(SELECTOR) as HTMLElement | null;
    if (!el) return;
    const rect = el.getBoundingClientRect();
    const x = ((e.clientX - rect.left) / rect.width) * 100;
    const y = ((e.clientY - rect.top) / rect.height) * 100;
    el.style.setProperty('--spot-x', `${x}%`);
    el.style.setProperty('--spot-y', `${y}%`);
  };

  document.addEventListener('pointermove', handler, { passive: true });
}
