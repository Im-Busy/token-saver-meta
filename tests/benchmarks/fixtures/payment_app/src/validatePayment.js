import { checkBalance } from './checkBalance.js';

export function validatePayment(card) {
  if (!card || !card.number) return false;
  const hasBalance = checkBalance(card.number, 100);
  return hasBalance && card.number.length === 16;
}
