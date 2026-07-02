import { validatePayment } from './validatePayment.js';

export function processPayment(amount, card) {
  const valid = validatePayment(card);
  if (!valid) throw new Error('Invalid card');
  return { status: 'processed', amount };
}
