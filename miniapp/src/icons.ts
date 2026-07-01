/**
 * Maps the icon-name strings used throughout the app (e.g. "fa-wallet",
 * stored on Account / Category rows) to Font Awesome icon definitions.
 *
 * Add new entries here when introducing new icons. We import individual icons
 * (not the whole library) so the bundle stays slim.
 */

import type { IconDefinition } from '@fortawesome/fontawesome-svg-core';
import {
  faArrowLeft,
  faArrowRight,
  faAward,
  faBagShopping,
  faBolt,
  faBriefcase,
  faBuildingColumns,
  faCar,
  faCartShopping,
  faChartLine,
  faCheck,
  faCircleMinus,
  faCirclePlus,
  faCreditCard,
  faFileInvoiceDollar,
  faFilm,
  faFire,
  faGift,
  faGraduationCap,
  faHandHoldingHeart,
  faHeartPulse,
  faHouse,
  faLaptopCode,
  faMobileScreen,
  faMoneyBillWave,
  faPen,
  faPiggyBank,
  faPlane,
  faPlus,
  faRepeat,
  faRightLeft,
  faShoePrints,
  faSpa,
  faTag,
  faTrashCan,
  faTrophy,
  faUtensils,
  faWallet,
  faWandMagicSparkles,
  faXmark,
} from '@fortawesome/free-solid-svg-icons';

const REGISTRY: Record<string, IconDefinition> = {
  // Account types
  'fa-wallet': faWallet,
  'fa-credit-card': faCreditCard,
  'fa-building-columns': faBuildingColumns,
  'fa-mobile-screen': faMobileScreen,
  'fa-chart-line': faChartLine,
  'fa-piggy-bank': faPiggyBank,
  'fa-money-bill-wave': faMoneyBillWave,

  // Categories
  'fa-tag': faTag,
  'fa-utensils': faUtensils,
  'fa-cart-shopping': faCartShopping,
  'fa-car': faCar,
  'fa-house': faHouse,
  'fa-file-invoice-dollar': faFileInvoiceDollar,
  'fa-heart-pulse': faHeartPulse,
  'fa-bag-shopping': faBagShopping,
  'fa-film': faFilm,
  'fa-graduation-cap': faGraduationCap,
  'fa-plane': faPlane,
  'fa-repeat': faRepeat,
  'fa-spa': faSpa,
  'fa-hand-holding-heart': faHandHoldingHeart,
  'fa-circle-minus': faCircleMinus,
  'fa-circle-plus': faCirclePlus,
  'fa-briefcase': faBriefcase,
  'fa-laptop-code': faLaptopCode,
  'fa-gift': faGift,

  // UI affordances
  'fa-plus': faPlus,
  'fa-pen': faPen,
  'fa-trash-can': faTrashCan,
  'fa-arrow-left': faArrowLeft,
  'fa-arrow-right': faArrowRight,
  'fa-right-left': faRightLeft,
  'fa-check': faCheck,
  'fa-xmark': faXmark,

  // Gamification / badges
  'fa-shoe-prints': faShoePrints,
  'fa-fire': faFire,
  'fa-award': faAward,
  'fa-trophy': faTrophy,
  'fa-wand-magic-sparkles': faWandMagicSparkles,
  'fa-bolt': faBolt,
};

export function resolveIcon(name: string | null | undefined): IconDefinition {
  if (!name) return faTag;
  return REGISTRY[name] ?? faTag;
}
